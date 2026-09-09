# Stage 1 第 1 课：从第一性原理推导 Agent Loop

模型无状态：一次 `model()` 只看你这次塞进去的 context。

Agent = 外围循环：Think → Act → Observe → 写回 context → 再 Think。

## 最小循环

```python
context = [user_task]   # 累积给模型的全部输入。删掉累积：第二步换算看不到 26。
steps = 0

while steps < max_steps:    # 强制停止在外围。删掉：模型若一直 tool_call，循环永不结束。
    steps += 1              # 步数由循环自己加。不要读 output.steps，模型不负责停。

    # Think：模型只能产出「调工具」或「最终回答」，不能自己执行工具。
    output = model(context, tools)

    # 默认成功停止：不再 tool_call。写诗、最终回答都靠这条。
    # 删掉：即使模型已经答完，循环仍会空转或再调一次 model。
    if not output.is_tool_call:
        return output.answer

    # Act：外围替模型执行。删掉：只有「想调工具」，世界里什么都没发生。
    observation = execute_tool(output.tool_call)
    # 工具异常应变成 observation 写回去，而不是让进程崩掉或 continue 空转。

    # Observe 写回：必须发生在下一圈 model() 之前。
    # 删掉这两行 = 情况 A：工具跑了，模型下一轮当没发生过。
    context.append(output.tool_call)
    context.append(observation)

# 强制退出：循环停了，不等于任务成功。
return "stopped: max_steps"
```

## 用这份代码走「北京气温 → 换华氏度」

第 1 圈：

- `context = [用户任务]`
- model → `get_weather("北京")`
- 执行 → `26`
- 写回 → `context = [用户任务, get_weather("北京"), 26]`

第 2 圈：

- model 看见 `26` → `celsius_to_fahrenheit(26)`
- 执行 → `78.8`
- 写回 → `context = [..., 26, celsius_to_fahrenheit(26), 78.8]`

第 3 圈：

- model 看见两个观察 → `北京约 26°C，即 78.8°F`
- 无 tool_call → return 最终回答

## 推导过程中走过的坑

1. `output.steps`：停止条件不能挂在模型输出上，用循环自己的 `steps`。
2. `tool_result = execute_tool(...)` 会覆盖上一次结果；要 append 进 context。
3. `task.append(tool_result)` 和 `model(prompt, task, tool_result)` 把「当前结果」和「累积历史」拆开了。统一成一个 context，每次 model 只吃这份累积输入。
4. `if steps > max_steps` 放在 `model()` 之后会多跑一轮；判断放在 `while` 条件上。
