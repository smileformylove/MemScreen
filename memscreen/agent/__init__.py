### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-02             ###
### license: MIT                 ###

"""
MemScreen Agent System

Provides intelligent agent capabilities with automatic input classification
and smart dispatch to appropriate handlers.
"""

# Import base agent
from .base_agent import BaseAgent, AgentConfig

# Import intelligent agent
from .intelligent_agent import IntelligentAgent, DispatchRule

# Import planner
from .planner import Planner, Plan, PlanStep

# Import skills
from .base_skill import BaseSkill, SkillRegistry, SkillResult

__all__ = [
    # Base Agent
    "BaseAgent",
    "AgentConfig",

    # Intelligent Agent
    "IntelligentAgent",
    "DispatchRule",

    # Planner
    "Planner",
    "Plan",
    "PlanStep",

    # Skills
    "BaseSkill",
    "SkillRegistry",
    "SkillResult",
]
