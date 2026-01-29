### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

"""
Base Agent for MemScreen Agent System

Integrates planning, skills, and memory into a unified agent.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

from .planner import Planner, Plan, PlanStep
from .base_skill import BaseSkill, SkillRegistry, SkillResult


@dataclass
class AgentConfig:
    """Configuration for an agent"""

    name: str = "MemScreen Agent"
    version: str = "1.0.0"
    description: str = "MemScreen AI Agent"
    max_parallel_steps: int = 3
    enable_memory: bool = True
    enable_learning: bool = True


class BaseAgent:
    """
    Base Agent class that integrates planning, skills, and memory.

    The agent can:
    - Plan tasks using the Planner
    - Execute skills via SkillRegistry
    - Remember and recall information using Memory
    - Learn from experience
    """

    def __init__(
        self,
        memory_system=None,
        llm_client=None,
        config: AgentConfig = None
    ):
        """
        Initialize the agent.

        Args:
            memory_system: Memory system for context storage
            llm_client: LLM client for AI capabilities
            config: Agent configuration
        """
        self.config = config or AgentConfig()
        self.memory_system = memory_system
        self.llm_client = llm_client

        # Initialize components
        self.skill_registry = SkillRegistry()
        self.planner = Planner(
            llm_client=llm_client,
            available_skills=self.skill_registry.list_skills()
        )

        # Agent state
        self.current_plan: Optional[Plan] = None
        self.execution_history: List[Dict[str, Any]] = []

        print(f"[Agent] Initialized {self.config.name} v{self.config.version}")

    def register_skill(self, skill: BaseSkill):
        """
        Register a skill with the agent.

        Args:
            skill: Skill instance to register
        """
        # Inject dependencies
        skill.memory_system = self.memory_system
        skill.llm_client = self.llm_client

        # Register
        self.skill_registry.register(skill)

        # Update planner's skill list
        self.planner.available_skills = self.skill_registry.list_skills()

    async def execute_goal(self, goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a goal by planning and executing steps.

        Args:
            goal: The goal to achieve
            context: Additional context for execution

        Returns:
            Execution results dictionary
        """
        print(f"[Agent] Executing goal: {goal}")

        execution_start = datetime.now()

        try:
            # 1. Create plan
            print("[Agent] Planning...")
            plan = await self.planner.create_plan(goal, context)
            self.current_plan = plan

            # 2. Execute plan
            print(f"[Agent] Executing plan with {len(plan.steps)} steps...")
            execution_result = await self._execute_plan(plan)

            # 3. Remember the experience
            if self.config.enable_memory and self.memory_system:
                await self._remember_execution(goal, plan, execution_result)

            # 4. Return results
            result = {
                "success": execution_result["success"],
                "goal": goal,
                "plan": plan.to_dict(),
                "results": execution_result["results"],
                "execution_time": (datetime.now() - execution_start).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }

            print(f"[Agent] Goal completed in {result['execution_time']:.2f}s")
            return result

        except Exception as e:
            print(f"[Agent] Error executing goal: {e}")
            return {
                "success": False,
                "goal": goal,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _execute_plan(self, plan: Plan) -> Dict[str, Any]:
        """
        Execute a plan step by step.

        Args:
            plan: Plan to execute

        Returns:
            Execution results
        """
        results = []
        plan.status = "in_progress"

        while not plan.is_complete():
            # Get pending steps (with dependencies met)
            pending_steps = plan.get_pending_steps()

            if not pending_steps:
                # No steps ready but plan not complete - circular dependency or error
                break

            # Execute ready steps (up to max_parallel)
            for step in pending_steps[:self.config.max_parallel_steps]:
                step.status = "in_progress"

            # Execute in parallel
            tasks = [
                self._execute_step(step)
                for step in pending_steps[:self.config.max_parallel_steps]
            ]

            step_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for step, result in zip(pending_steps[:self.config.max_parallel_steps], step_results):
                if isinstance(result, Exception):
                    step.status = "failed"
                    step.error = str(result)
                    results.append({
                        "step_id": step.step_id,
                        "success": False,
                        "error": str(result)
                    })
                else:
                    step.status = "completed"
                    step.result = result.data
                    results.append({
                        "step_id": step.step_id,
                        "success": result.success,
                        "data": result.data,
                        "metadata": result.metadata
                    })

            # Small delay between batches
            await asyncio.sleep(0.1)

        # Update plan status
        if all(s.status == "completed" for s in plan.steps):
            plan.status = "completed"
            success = True
        else:
            plan.status = "failed"
            success = False

        return {
            "success": success,
            "results": results,
            "plan_status": plan.status
        }

    async def _execute_step(self, step: PlanStep) -> SkillResult:
        """
        Execute a single plan step.

        Args:
            step: PlanStep to execute

        Returns:
            SkillResult
        """
        print(f"[Agent] Executing step {step.step_id}: {step.description}")

        # Get skill
        skill = self.skill_registry.get(step.skill_name)
        if not skill:
            return SkillResult(
                success=False,
                data=None,
                error=f"Skill '{step.skill_name}' not found"
            )

        # Validate parameters
        is_valid, error_msg = skill.validate_parameters(**step.parameters)
        if not is_valid:
            return SkillResult(
                success=False,
                data=None,
                error=f"Parameter validation failed: {error_msg}"
            )

        # Execute skill
        try:
            start_time = datetime.now()
            result = await skill.execute(**step.parameters)
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time

            print(f"[Agent] Step {step.step_id} completed in {execution_time:.2f}s")
            return result

        except Exception as e:
            print(f"[Agent] Step {step.step_id} failed: {e}")
            return SkillResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def _remember_execution(
        self,
        goal: str,
        plan: Plan,
        execution_result: Dict[str, Any]
    ):
        """
        Remember the execution in memory.

        Args:
            goal: The goal that was executed
            plan: The plan that was created
            execution_result: Results of execution
        """
        try:
            # Create procedural memory
            memory_data = {
                "task_objective": goal,
                "plan": plan.to_dict(),
                "execution_results": execution_result,
                "timestamp": datetime.now().isoformat()
            }

            # Add to memory
            if hasattr(self.memory_system, 'add'):
                await self.memory_system.add(
                    content=f"Executed goal: {goal}",
                    memory_type="procedural",
                    metadata=memory_data
                )
                print("[Agent] Saved execution to memory")

        except Exception as e:
            print(f"[Agent] Error saving to memory: {e}")

    async def use_skill(self, skill_name: str, **kwargs) -> SkillResult:
        """
        Directly use a skill without planning.

        Args:
            skill_name: Name of skill to use
            **kwargs: Parameters for the skill

        Returns:
            SkillResult
        """
        skill = self.skill_registry.get(skill_name)
        if not skill:
            return SkillResult(
                success=False,
                data=None,
                error=f"Skill '{skill_name}' not found"
            )

        return await skill.execute(**kwargs)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.

        Returns:
            Status dictionary
        """
        return {
            "name": self.config.name,
            "version": self.config.version,
            "current_plan": self.current_plan.to_dict() if self.current_plan else None,
            "available_skills": self.skill_registry.list_skills(),
            "execution_history_count": len(self.execution_history)
        }


__all__ = [
    "BaseAgent",
    "AgentConfig"
]
