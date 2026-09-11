from dataclasses import dataclass

from context import build
from memory import Memory, Step
from model import Model, ModelOutput
from tools import ToolRegistry, ToolResult


@dataclass
class Agent:
    model: Model
    registry: ToolRegistry
    max_steps: int = 6

    def run(self, task: str) -> str:
        memory: Memory = Memory(task=task)
        steps: int = 0
        while steps < self.max_steps:
            steps += 1
            output: ModelOutput = self.model.generate(build(memory), self.registry.schema())
            if output.kind == "final_answer":
                return output.content or ""
            result: ToolResult = self.registry.execute(output.name or "", output.arguments or {})
            memory.append(
                Step(
                    tool_call={
                        "id": output.tool_call_id,
                        "name": output.name,
                        "arguments": output.arguments
                    },
                    observation=result.observation if result.ok else None,
                    error=None if result.ok else result.observation,
                )
            )
        return "stopped: max_steps"
