# Stage 1 第 6 课：CONTEXT / TOOL

第 5 课：Memory 是仓库，Context 是派生。这课回答两句：

```text
一次 generate，模型到底看见哪些输入？
Tool 从注册到观察回灌，中间经过哪几步？
```

对照温度任务 **Step 2**：即将调用 `celsius_to_fahrenheit` 的那一次 `generate`。

## Context 清单

`write_memory_to_messages`（`agents.py` 758）按固定顺序拼接：

```text
1. memory.system_prompt.to_messages()
2. 按顺序每个 memory.steps[i].to_messages()
```

Step 2 开始时 `steps` 里已有：`TaskStep` + 第 1 圈完成的 `ActionStep`。

| 块 | 来源 | 角色 | Step 2 时模型看见什么 |
|---|---|---|---|
| A | `initialize_system_prompt`（1265）把 `self.tools` 填进模板；`SystemPromptStep.to_messages`（`memory.py` 200） | SYSTEM | 工具名/描述/参数：`get_celsius`、`celsius_to_fahrenheit`、`final_answer`。并写明结束必须调 `final_answer` |
| B | `TaskStep.to_messages`（191） | USER | `New task:` + 「北京现在多少摄氏度？再把它换成华氏度。」 |
| C | `ActionStep.to_messages`（92）：`model_output`、`tool_calls` | ASSISTANT / TOOL_CALL | 上一圈要调 `get_celsius(city=北京)` |
| D | 同一函数（126）：`observations` | TOOL_RESPONSE | `Observation:\n26.0` |

拼起来：

```text
SYSTEM        工具清单 + 必须用 final_answer 结束
USER          New task: 北京气温再换华氏度
TOOL_CALL     get_celsius(北京)
TOOL_RESPONSE Observation: 26.0
```

`ActionStep.model_input_messages` **不是**第 5 块。那是上一圈存档的拷贝，不会再经 `to_messages` 拼进这一圈。

第二条发现通道不在 messages 正文里：`model.generate(..., tools_to_call_from=...)`（`agents.py` 1309–1312）把 schema 交给 API。模型发现工具 = 系统提示里的清单 + 这次参数。

## 为什么 Tool Result 必须回到 Context

D 就是第 1 课的回灌。没有 `Observation: 26.0`，Step 2 的模型仍只看见任务原文，会再调 `get_celsius` 或编一个温度。

回灌路径仍是第 4 课那三个函数：写入 `ActionStep.observations` → `memory.steps.append` → 下一圈 `write_memory_to_messages` 变成 TOOL_RESPONSE。

## Tool 生命周期

| 阶段 | 谁在做 | 位置 |
|---|---|---|
| 注册 | `@tool` 把函数变成 `Tool`（name / description / inputs）；`_setup_tools` 放进 `self.tools`；`setdefault("final_answer", FinalAnswerTool())` | `tools.py` 的 `tool()`；`agents.py` 389–402 |
| 发现 | 系统提示渲染 `tool.to_tool_calling_prompt()`；`generate(tools_to_call_from=...)` | 模板 `toolcalling_agent.yaml`；`agents.py` 1312 |
| 调用 | 模型产出 `chat_message.tool_calls`（没有则 `parse_tool_calls`） | `agents.py` 1327–1334 |
| 执行 | `process_tool_calls` → `execute_tool_call` → `tool(**arguments)` | `agents.py` 1361、1453、1486 |
| 返回 | 结果变成字符串 `observation`，写入当前 `ActionStep` | `agents.py` 1401、1436–1440 |
| 失败 | `execute_tool_call` 抛 `AgentToolExecutionError`；`_run_stream` 记到 `action_step.error`；`to_messages` 把 error 编成 TOOL_RESPONSE，下一圈模型能看见 | `agents.py` 1490–1502、597–599；`memory.py` 138–148 |
| 鉴权 | Stage 1 几乎没有。只检查工具在不在表里、参数能不能过 schema。Permission / Sandbox 不是这课 | `agents.py` 1464–1476 |

`final_answer` 也走同一条执行链，只是名字特殊：`is_final_answer = tool_name == "final_answer"`。

## 和第 5 课的边界

- Memory：`steps` 里的 `TaskStep` / `ActionStep`
- Context：上面 A–D（外加 `tools_to_call_from`）
- Tool：把世界里的一次执行，变成 Context 里的一段 `Observation:`

不在这课：MCP、长期记忆、Planner、真正的权限模型。
