### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

"""
Task Planner for MemScreen Agent System

Breaks down goals into executable steps using LLM.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import re


@dataclass
class PlanStep:
    """A single step in a plan"""

    step_id: int
    description: str
    skill_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)  # Step IDs this depends on
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "skill_name": self.skill_name,
            "parameters": self.parameters,
            "depends_on": self.depends_on,
            "status": self.status,
            "error": self.error
        }


@dataclass
class Plan:
    """A complete execution plan"""

    plan_id: str
    goal: str
    steps: List[PlanStep]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "created"  # created, in_progress, completed, failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at,
            "status": self.status
        }

    def get_pending_steps(self) -> List[PlanStep]:
        """Get steps that are ready to execute (no unmet dependencies)"""
        completed_step_ids = {s.step_id for s in self.steps if s.status == "completed"}
        pending = []

        for step in self.steps:
            if step.status == "pending":
                # Check if all dependencies are met
                if all(dep_id in completed_step_ids for dep_id in step.depends_on):
                    pending.append(step)

        return pending

    def is_complete(self) -> bool:
        """Check if all steps are complete"""
        return all(s.status in ["completed", "failed"] for s in self.steps)

    def get_progress(self) -> float:
        """Get plan progress as percentage"""
        if not self.steps:
            return 1.0

        completed = sum(1 for s in self.steps if s.status == "completed")
        return completed / len(self.steps)


class Planner:
    """
    Task planner that breaks down goals into executable steps.
    """

    def __init__(self, llm_client, available_skills: List[str] = None):
        """
        Initialize the planner.

        Args:
            llm_client: LLM client for generating plans
            available_skills: List of available skill names
        """
        self.llm_client = llm_client
        self.available_skills = available_skills or []

    async def create_plan(self, goal: str, context: Dict[str, Any] = None) -> Plan:
        """
        Create an execution plan for the given goal.

        Args:
            goal: The goal to achieve
            context: Additional context for planning

        Returns:
            Plan object with executable steps
        """
        # Build planning prompt
        prompt = self._build_planning_prompt(goal, context)

        # Generate plan using LLM
        response = await self._generate_plan(prompt)

        # Parse response into Plan object
        plan = self._parse_plan(goal, response)

        return plan

    def _build_planning_prompt(self, goal: str, context: Dict[str, Any] = None) -> str:
        """Build the planning prompt for the LLM."""

        skills_list = "\n".join(f"- {skill}" for skill in self.available_skills)

        prompt = f""" MemScreen 

## 
{goal}

## 
{skills_list}

## 

1. **** 2-5 
2. ****
3. ****
4. ****

## 

 JSON 

```json
{{
  "steps": [
    {{
      "step_id": 1,
      "description": "",
      "skill_name": "",
      "parameters": {{
        "param1": "value1"
      }},
      "depends_on": []
    }},
    {{
      "step_id": 2,
      "description": "",
      "skill_name": "",
      "parameters": {{}},
      "depends_on": [1]
    }}
  ]
}}
```

## 

- 
- 
- step_id  1 
- depends_on  ID
- parameters 

 JSON
"""

        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            prompt += f"\n\n## \n{context_str}\n"

        return prompt

    async def _generate_plan(self, prompt: str) -> str:
        """Generate plan using LLM."""
        try:
            if hasattr(self.llm_client, 'generate_response'):
                response = self.llm_client.generate_response(
                    messages=[{"role": "user", "content": prompt}]
                )
                return response
            else:
                # Fallback for different LLM interfaces
                return str(self.llm_client)
        except Exception as e:
            print(f"[Planner] Error generating plan: {e}")
            # Return a simple default plan
            return self._get_default_plan()

    def _get_default_plan(self) -> str:
        """Get a default plan when LLM fails."""
        return json.dumps({
            "steps": [
                {
                    "step_id": 1,
                    "description": "",
                    "skill_name": "analyze",
                    "parameters": {},
                    "depends_on": []
                }
            ]
        })

    def _parse_plan(self, goal: str, response: str) -> Plan:
        """Parse LLM response into Plan object."""
        try:
            # Extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response

            plan_data = json.loads(json_str)

            # Create PlanSteps
            steps = []
            for step_data in plan_data.get("steps", []):
                step = PlanStep(
                    step_id=step_data["step_id"],
                    description=step_data["description"],
                    skill_name=step_data["skill_name"],
                    parameters=step_data.get("parameters", {}),
                    depends_on=step_data.get("depends_on", [])
                )
                steps.append(step)

            # Sort by step_id
            steps.sort(key=lambda s: s.step_id)

            # Create Plan
            plan = Plan(
                plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                goal=goal,
                steps=steps
            )

            print(f"[Planner] Created plan with {len(steps)} steps")
            return plan

        except Exception as e:
            print(f"[Planner] Error parsing plan: {e}")
            # Return a simple fallback plan
            return Plan(
                plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                goal=goal,
                steps=[
                    PlanStep(
                        step_id=1,
                        description="",
                        skill_name="general",
                        parameters={"goal": goal},
                        depends_on=[]
                    )
                ]
            )


__all__ = [
    "Plan",
    "PlanStep",
    "Planner"
]
