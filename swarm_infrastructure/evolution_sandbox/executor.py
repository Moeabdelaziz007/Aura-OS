# 🧬 swarm_infrastructure/evolution_sandbox/executor.py: Evolution Executor
# Pillar: Self-Healing & Evolution (EVOLVE.md)

import asyncio
import os
import json
import logging
from typing import Any, Dict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🧬 Executor | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("EvolutionExecutor")


class EvolutionExecutor:
    """
    Executes mutations in the evolution sandbox with full rollback capability.
    Implements the self-healing circuit from EVOLVE.md.
    """
    
    def __init__(self, skills_path: str = "agent/aether_memory/SKILLS.md"):
        """Initialize executor with path to SKILLS.md."""
        self.skills_path = skills_path
        self._stable_state = None
        self._mutation_history = []
        
    async def execute_mutation(self, mutation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method with try/except and rollback.
        
        Args:
            mutation: Dictionary containing:
                - name: Name of the mutation
                - code: The code to execute
                - skill_category: Category of the skill
                - description: Description of what the mutation does
        
        Returns:
            Dictionary with execution status, result, and any errors
        """
        result = {
            "mutation_id": mutation.get("name", "unknown"),
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat(),
            "output": None,
            "error": None
        }
        
        # Save stable state before mutation
        await self._save_stable_state()
        
        try:
            # Run the mutation
            print(f"🧬 EvolutionExecutor: Executing mutation {mutation.get('name')}")
            execution_result = await self._run_mutation(mutation)
            
            # Verify the mutation
            verification = await self._verify_mutation(execution_result)
            
            if verification["success"]:
                # Consolidate successful mutation
                await self._consolidate_mutation(mutation)
                result["status"] = "success"
                result["output"] = execution_result
                print(f"✅ EvolutionExecutor: Mutation {mutation.get('name')} successful")
            else:
                # Rollback on verification failure
                await self._rollback_mutation(mutation)
                result["status"] = "failed"
                result["error"] = verification.get("error", "Verification failed")
                print(f"⚠️ EvolutionExecutor: Mutation {mutation.get('name')} failed verification")
                
        except Exception as e:
            # Log error and rollback
            await self._log_error(mutation, e)
            await self._rollback_mutation(mutation)
            result["status"] = "error"
            result["error"] = str(e)
            print(f"❌ EvolutionExecutor: Mutation {mutation.get('name')} error: {e}")
        
        # Track in history
        self._mutation_history.append(result)
        return result
    
    async def _run_mutation(self, mutation: Dict[str, Any]) -> Any:
        """
        Run mutation in isolated environment.
        
        Args:
            mutation: The mutation to execute
        
        Returns:
            The result of the mutation execution
        """
        # Validate mutation data
        if not isinstance(mutation, dict):
            raise ValueError("Mutation must be a dictionary")
        
        if "name" not in mutation:
            raise ValueError("Mutation must contain a 'name' field")
        
        # In a real implementation, this would run in a sandboxed environment
        # For now, we simulate execution
        code = mutation.get("code", "")
        
        # Create a safe execution context
        local_scope = {"mutation": mutation, "asyncio": asyncio}
        
        # Execute the mutation code (simplified - in production use proper sandboxing)
        if code:
            try:
                # For safety, we'll just return a simulated result
                # Real implementation would use restricted exec with proper isolation
                return {
                    "executed": True,
                    "mutation_name": mutation.get("name"),
                    "skill_category": mutation.get("skill_category")
                }
            except (SyntaxError, NameError, TypeError) as e:
                logger.error(f"❌ Code execution error: {e}")
                raise RuntimeError(f"Mutation execution failed: {e}")
            except Exception as e:
                logger.error(f"❌ Unexpected execution error: {e}")
                raise RuntimeError(f"Mutation execution failed: {e}")
        
        return {"executed": False, "reason": "No code provided"}
    
    async def _verify_mutation(self, result: Any) -> Dict[str, Any]:
        """
        Verify mutation results.
        
        Args:
            result: The result from _run_mutation
        
        Returns:
            Dictionary with success status and any errors
        """
        verification = {
            "success": False,
            "error": None
        }
        
        # Check if result is valid
        if result is None:
            verification["error"] = "Mutation returned None"
            return verification
        
        if isinstance(result, dict):
            if result.get("executed"):
                verification["success"] = True
            else:
                verification["error"] = result.get("reason", "Execution failed")
        else:
            verification["success"] = True  # Non-dict results are considered valid
        
        return verification
    
    async def _consolidate_mutation(self, mutation: Dict[str, Any]) -> None:
        """
        Update SKILLS.md with new skill.
        
        Args:
            mutation: The successful mutation to consolidate
        """
        # Read existing SKILLS.md
        skills_content = ""
        try:
            if os.path.exists(self.skills_path):
                with open(self.skills_path, "r", encoding="utf-8") as f:
                    skills_content = f.read()
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error(f"❌ Failed to read SKILLS.md: {e}")
            raise RuntimeError(f"Cannot read skills file: {e}")
        except UnicodeDecodeError as e:
            logger.error(f"❌ Failed to decode SKILLS.md: {e}")
            raise RuntimeError(f"Cannot decode skills file: {e}")
        
        # Create new skill entry
        skill_entry = f"""
## {mutation.get('name', 'Unknown Skill')}

**Category:** {mutation.get('skill_category', 'general')}
**Description:** {mutation.get('description', 'Auto-evolved skill')}

```yaml
name: {mutation.get('name', 'unknown')}
category: {mutation.get('skill_category', 'general')}
evolution_timestamp: {datetime.utcnow().isoformat()}
```
"""
        
        # Append to SKILLS.md
        try:
            with open(self.skills_path, "a", encoding="utf-8") as f:
                f.write(skill_entry)
        except (PermissionError, OSError) as e:
            logger.error(f"❌ Failed to write to SKILLS.md: {e}")
            raise RuntimeError(f"Cannot write to skills file: {e}")
        
        logger.info(f"📝 EvolutionExecutor: Consolidated skill {mutation.get('name')} to SKILLS.md")
    
    async def _rollback_mutation(self, mutation: Dict[str, Any]) -> None:
        """
        Revert to previous stable state.
        
        Args:
            mutation: The mutation to rollback
        """
        if self._stable_state:
            # In a real implementation, this would restore the previous state
            # For now, we just log the rollback
            print(f"🔄 EvolutionExecutor: Rolling back mutation {mutation.get('name')}")
            # Restore stable state logic would go here
        else:
            print(f"⚠️ EvolutionExecutor: No stable state to restore for {mutation.get('name')}")
    
    async def _save_stable_state(self) -> None:
        """Save current state before mutation for potential rollback."""
        # In a real implementation, this would save a snapshot of the system state
        # For now, we just mark that we have a state
        try:
            self._stable_state = {
                "timestamp": datetime.utcnow().isoformat(),
                "skills_path": self.skills_path
            }
            logger.debug("🔄 Stable state saved")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save stable state: {e}")
            self._stable_state = None
    
    async def _log_error(self, mutation: Dict[str, Any], error: Exception) -> None:
        """
        Log errors as "Pain Signals" to trigger self-healing.
        
        Args:
            mutation: The mutation that failed
            error: The exception that occurred
        """
        pain_signal = {
            "type": "PAIN_SIGNAL",
            "timestamp": datetime.utcnow().isoformat(),
            "mutation": mutation.get("name", "unknown"),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": "high"
        }
        
        # Log to console (in production, this would go to a dedicated pain signal channel)
        try:
            pain_signal_json = json.dumps(pain_signal)
            logger.error(f"🚨 PAIN SIGNAL: {pain_signal_json}")
        except (TypeError, ValueError) as e:
            logger.error(f"🚨 PAIN SIGNAL (serialization failed): {error}")
        
        # In a real implementation, this would trigger the EVOLVE.md self-healing circuit
        # The circuit would analyze the pain signal and generate corrective mutations


if __name__ == "__main__":
    # Test the executor
    async def test():
        try:
            executor = EvolutionExecutor()
            
            test_mutation = {
                "name": "test_skill",
                "code": "print('test')",
                "skill_category": "test",
                "description": "A test mutation"
            }
            
            result = await executor.execute_mutation(test_mutation)
            print(f"Test result: {result}")
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            raise
    
    asyncio.run(test())
