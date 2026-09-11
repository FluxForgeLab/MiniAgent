from dataclasses import dataclass, field
from typing import Any


@dataclass
class Step:
    tool_call: dict[str, Any] | None = None
    observation: str | None = None
    error: str | None = None


@dataclass
class Memory:
    task: str
    steps: list[Step] = field(default_factory=list)

    def append(self, step: Step) -> None:
        self.steps.append(step)