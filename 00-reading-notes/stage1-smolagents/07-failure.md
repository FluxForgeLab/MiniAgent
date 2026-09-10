# Stage 1 第 7 课：FAILURE（本轮收束）

读 smolagents 的最后一课。FAILURE 已对照源码讲完。路线图里的 MODIFY（给 smolagents 加 `StopCondition`）**本课不做**：下一节在自己的 Mini Agent 里实现停止条件，比改 vendor 更接近 Stage 1 目标。

## 总闸门

`_run_stream`（`agents.py` 577–611）把失败分成三条路：

```text
AgentGenerationError / interrupt  → 炸出循环
其它 AgentError                   → 记到 step.error，当观察，再试一圈
max_steps                         → while 自己停，再补一次强制收尾
```

```577:604:vendor/smolagents/src/smolagents/agents.py
            try:
                for output in self._step_stream(action_step):
                    ...
                    if isinstance(output, ActionOutput) and output.is_final_answer:
                        returned_final_answer = True
            except AgentGenerationError as e:
                raise e
            except AgentError as e:
                action_step.error = e
            finally:
                self._finalize_step(action_step)
                self.memory.steps.append(action_step)
                yield action_step
                self.step_number += 1
```

类型树在 `utils.py` 92–137：

```text
AgentError
├── AgentGenerationError
├── AgentParsingError
├── AgentExecutionError
│     ├── AgentToolCallError
│     └── AgentToolExecutionError
└── AgentMaxStepsError
```

## 失败矩阵

| 失败 | 循环 | 写入 Memory | 下一圈模型能否看见 |
|---|---|---|---|
| 工具抛错 / 参数错（`AgentToolExecutionError` / `AgentToolCallError`） | 继续（未到 max_steps） | 是，`action_step.error` | 能。`to_messages` 编成 `Error:\n...` 的 TOOL_RESPONSE（`memory.py` 138–148） |
| 解析失败 `AgentParsingError` | 同上 | 同上 | 同上 |
| `AgentGenerationError` | **停**，异常冲出 `run` | `finally` 仍 append，但通常不写 `error` 字段 | 没有下一圈 |
| 走到 `max_steps` | **停**（强制） | 是。`_handle_max_steps_reached` 再 append 一个带 `AgentMaxStepsError` 的 step，并再调一次模型挤答案 | 没有下一圈 |
| `interrupt_switch` | **停**。在 try **之外** `raise AgentError`（546–547） | 当前圈不写；旧 steps 还在 | 没有下一圈 |

和第 1 课对齐：工具失败要变成可被下一圈看见的观察，不要默默空转，也不要把所有错误都当成进程崩溃。smolagents 用 `error` 字段表达可恢复失败，用 `raise` 表达不可恢复失败。

## MODIFY：本课刻意不做

路线图点名：给 smolagents 增加或收紧 `StopCondition`。

现成停止只有：

- 成功：`final_answer` → `returned_final_answer`
- 强制：`max_steps`、`interrupt_switch`

缺的是可插拔条件（例如：同一工具相同参数连续 N 次、总 token 超限、连续解析失败 N 次）。这些放到 Mini Agent 的 `run/step/stop` 里自己做，不改 `vendor/`。

## 第 1–7 课读源码收束

可以不依赖框架讲清：

| 课 | 钉死的机制 |
|---|---|
| 1 | Agent = 外围循环；观察必须回灌；成功停 ≠ 强制停 |
| 2 | smolagents 成功停是 `final_answer`，不是「不再 tool call」 |
| 3 | 温度三步 + 写诗一步，都亲眼跑过 |
| 4 | `run → _run_stream → _step_stream → generate → execute_tool_call` |
| 5 | Memory 是仓库；Context 是派生；模型选 Act，`while` 选是否再 step |
| 6 | Step 2 的 A–D 输入；Tool 注册→发现→执行→回灌 |
| 7 | 可恢复失败进 `step.error`；生成失败 / 中断炸出循环 |

下一节重头戏：**自己设计并实现 Mini Agent v1**（约 500–1000 行：`agent` / `model` / `tools` / `memory` / `context` / `main`）。不抄 smolagents，但必须能映射到上面这些机制。Planner、MCP、长期 Memory 仍然不做。
