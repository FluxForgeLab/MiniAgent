# Stage 1 第 2 课：smolagents WHY / WHAT

对照第 1 课的最小循环读源码，只回答：它在替你省掉什么，核心抽象是什么。不写用法说明书。

源码位置：`vendor/smolagents/src/smolagents/`

## WHY

smolagents 解决的是 ReAct 外围循环：

```text
task → think → act → observation → think → …
```

模型本身无状态，一次 `generate()` 只吐文本。没有这个项目，开发者必须自己做：

- 控制循环（步数、何时停）
- 组装 context
- 解析模型输出（tool call 或 code）
- 真正执行工具 / 代码
- 把 observation 写回，供下一轮 thinking 使用
- 区分成功停止和强制停止

它不是「帮你调 LLM API」。只会调 API 的话，和第 1 课的 `model()` 没有区别。

## WHAT

对外提供的是：**带 Tool / Memory 的多步 Agent Runtime**。

tool 列表不是产品本身，只是这个 Runtime 能调用的能力。

核心抽象：

| 抽象 | 职责 |
|---|---|
| `MultiStepAgent` | 基类。拥有 `while` 循环、`max_steps`、把 step 写入 Memory |
| `ToolCallingAgent` | Act 语言 = 结构化 tool call（名字 + 参数） |
| `CodeAgent` | Act 语言 = Python 代码；`python_executor` 是执行器，不是语言 |
| `Memory` / `ActionStep` | 本轮对话的累积状态（不是长期记忆） |
| `Tool` | 可调用能力：name / schema / execute |

## 和第 1 课的对照

| 第 1 课概念 | smolagents 里谁在做 | 依据 |
|---|---|---|
| `while steps < max_steps` | `MultiStepAgent._run_stream` | `agents.py` 约 545 行：`while not returned_final_answer and self.step_number <= max_steps` |
| `model(context, tools)` | 子类 `_step_stream` 里的 `model.generate` | `ToolCallingAgent` 约 1309 行；`CodeAgent` 约 1677 行。578 行只是基类在调度 `_step_stream`，不是 model 调用 |
| `if not tool_call: return` | **不一致**。成功停止是 `ActionOutput.is_final_answer` | 基类约 582–592 行把 `returned_final_answer = True` |
| `execute_tool(...)` | `ToolCallingAgent.process_tool_calls` → `execute_tool_call`；`CodeAgent` 则 `python_executor(code)` | 约 1361、1453、1726 行 |
| `context.append(observation)` | Memory 三步回灌，不是直接 append 到 list | 见下一节 |

## 成功停止：和第 1 课的关键差异

第 1 课默认成功停止：模型不再请求 tool call，直接给最终回答。

smolagents 不是这样。基类只认一个统一信号：

```text
ActionOutput.is_final_answer == True
→ returned_final_answer = True
→ while 结束
```

「结束」本身也是一次 Act：

| | ToolCallingAgent | CodeAgent |
|---|---|---|
| Act 语言 | 结构化 tool call | Python 代码 |
| 谁执行 | `execute_tool_call` | `python_executor` |
| 成功停止 | 调用名为 `final_answer` 的工具 | 代码里调用 `final_answer(...)`，执行器捕获 `FinalAnswerException`，置 `is_final_answer=True` |

`ToolCallingAgent` 在约 1327 行：若模型没给出结构化 tool_calls，会尝试从文本 parse；失败则抛 `AgentParsingError`。这不是「说一段人话就算成功结束」。

强制停止仍是 `max_steps`（约 545、606 行）。强制退出 ≠ 任务成功。

## Observation 如何回到下一轮模型

对应第 1 课的 `context.append(observation)`，这里拆成三步：

1. 把 observation 写进当前 `ActionStep`  
   `process_tool_calls` 末尾约 1436–1440 行（CodeAgent 则写 `memory_step.observations`，约 1754 行）
2. `_run_stream` 的 `finally` 里 `self.memory.steps.append(action_step)`（约 602 行）
3. 下一圈 `_step_stream` 开头 `write_memory_to_messages()`（约 758、1284 / 1646 行）把 Memory 编成 messages，再交给 `model.generate`

Memory 是累积 context 的仓库；`write_memory_to_messages` 才是下一轮 `model()` 的输入从哪来。

## 暂不深入

- `planning_interval` / PlanningStep：Planner，不是 Stage 1 最小循环
- Tokenizer、模型权重、GPU、推理内核：在 Model API 之下
- MCP、长期 Memory、多 Agent：后续阶段

## 第 2 课自检

拿掉 smolagents 之后，仍然能讲清：

1. 它省掉的是外围 ReAct Runtime，不是 LLM 调用本身
2. 两种 Agent 的差别是 Act 语言，不是「一个能用工具、一个不能」
3. 成功停止靠 `final_answer`，不是「不再 tool call」
4. 观察必须进 Memory，再变成下一轮 messages
