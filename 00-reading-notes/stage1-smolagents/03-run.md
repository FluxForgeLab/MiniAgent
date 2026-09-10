# Stage 1 第 3 课：RUN 最小 Demo

对照第 1、2 课的循环，记录两次真实运行，不写源码调用链。

## 环境

- 模型：`OpenAIModel` + `kimi-k3`（Moonshot OpenAI 兼容接口）
- Agent：`ToolCallingAgent`，`max_steps=6`
- 工具：`get_celsius`（写死返回 `26.0`）、`celsius_to_fahrenheit`、框架自动注册的 `final_answer`
- 脚本：`00-reading-notes/stage1-smolagents/run_demo.py`
- 安装：`pip install -e vendor/smolagents`，密钥从仓库根目录 `.env` 读取
- 两次都跑通，不是只看 README

## 实验 1：两步工具任务

任务：`北京现在多少摄氏度？再把它换成华氏度。`

| Step | 模型要调什么 | 观察 | 是否 final_answer |
|---|---|---|---|
| 1 | `get_celsius` `city=北京` | `26.0` | 否 |
| 2 | `celsius_to_fahrenheit` `c=26` | `78.8` | 否 |
| 3 | `final_answer` `answer=北京现在 26.0°C，换算成华氏度是 78.8°F。` | 同上最终句 | 是 |

- `RESULT` 与 `Final answer` 一致：`北京现在 26.0°C，换算成华氏度是 78.8°F。`
- 停止方式：成功停止（`final_answer`），未碰到 `max_steps`
- Input tokens：1209 → 2504 → 3915，每圈 context 变长，说明观察进了下一轮输入
- Step 2 的参数是 `26` 而不是乱猜的温度，说明 Step 1 的观察回灌了

## 实验 2：写诗

任务：`写一首五言绝句，不要调用任何工具。`  
同一套 Agent 和工具表，单独 `run`，不和实验 1 连跑。

| Step | 模型要调什么 | 观察 | 是否 final_answer |
|---|---|---|---|
| 1 | `final_answer`（诗本身作为 answer） | `月落寒江夜，星垂远树低。孤舟随梦远，吹到小桥西。` | 是 |

- 没有调用 `get_celsius` / `celsius_to_fahrenheit`
- 停止方式：仍是 `Final answer:`，不是「说一段人话就直接 return」
- 1 步结束，未碰到 `max_steps`

## 和预期的差异

跑前预期：

1. 会先看到工具调用，而不是先看到最终答案 —— 实验 1 符合（先 `get_celsius`）
2. 两步工具任务至少 3 圈，最后一圈是 `final_answer` —— 符合
3. 写诗仍会走 `final_answer` —— 符合

写诗时温度工具没被调用，这不是异常：工具在表里 ≠ 每一步都必须用。模型认为写诗不需要查温度，只做「宣布结束」这一次 Act。

和第 1 课的差异再次被运行证实：smolagents 的成功停止是调用 `final_answer`，不是「不再 tool call」。写诗也是一次 tool call。
