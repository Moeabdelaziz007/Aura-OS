"""
🧬 Aether Forge — Data Models & Protocols
Disciplined data contracts for the Sovereign OS.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Protocol
import json

@dataclass(frozen=True)
class NanoAgent:
    """A single-purpose, ephemeral agent. Born. Executes. Dies."""
    id: str
    intent: str
    service: str
    born_at: datetime = field(default_factory=datetime.utcnow)
    energy_credits: int = 100

    @property
    def age_ms(self) -> float:
        return (datetime.utcnow() - self.born_at).total_seconds() * 1000

@dataclass
class ForgeResult:
    """The crystallized payload returned after agent self-destruction."""
    success: bool
    data: Optional[Dict[str, Any]]
    service: str
    execution_ms: float
    agent_id: str
    dna_crystallized: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def display(self) -> str:
        status_icon = "✅" if self.success else "❌"
        line = "━" * 60
        payload = json.dumps(self.data, indent=2, ensure_ascii=False) if self.success else f"Error: {self.error}"
        return (
            f"\n{line}\n"
            f"{status_icon} AETHER FORGE: {'DISSOLVED SUCCESSFULLY' if self.success else 'DISSOLUTION FAILED'}\n"
            f"{line}\n"
            f"🎯 Service    : {self.service.upper()}\n"
            f"⚡ Speed      : {self.execution_ms:.2f}ms\n"
            f"🧬 DNA Status : {'Crystallized (System 1 Active)' if self.dna_crystallized else 'Synthesized (System 2)'}\n"
            f"💥 Agent ID   : {self.agent_id} (Terminated)\n"
            f"{'─' * 60}\n"
            f"{payload}\n"
            f"{line}\n"
        )

@dataclass
class AgentProposal:
    """A proposal for action from a Nano-Agent for deliberation."""
    agent_id: str
    action: str
    confidence: float
    reasoning: str

class NanoExecutor(Protocol):
    """Protocol for API-native executors (The Synaptic Bonds)."""
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ...
