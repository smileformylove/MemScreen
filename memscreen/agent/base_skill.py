### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                 ###

"""
Base Skill Class for MemScreen Agent System

All skills should inherit from BaseSkill and implement the execute method.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SkillResult:
    """Result returned by a skill execution"""

    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    execution_time: float = 0.0

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SkillParameter:
    """Defines a parameter for a skill"""

    name: str
    type: type
    required: bool = True
    description: str = ""
    default: Any = None


class BaseSkill(ABC):
    """
    Base class for all skills in the MemScreen Agent system.

    Skills are reusable capabilities that an agent can use to accomplish tasks.
    """

    # Skill metadata (to be overridden by subclasses)
    name: str = "base_skill"
    description: str = "Base skill class"
    version: str = "1.0.0"
    parameters: List[SkillParameter] = []

    def __init__(self, memory_system=None, llm_client=None):
        """
        Initialize the skill.

        Args:
            memory_system: Optional memory system for context
            llm_client: Optional LLM client for AI capabilities
        """
        self.memory_system = memory_system
        self.llm_client = llm_client

    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the skill with the given parameters.

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult containing execution result
        """
        pass

    def validate_parameters(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters.

        Args:
            **kwargs: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Required parameter '{param.name}' is missing"

            if param.name in kwargs:
                value = kwargs[param.name]
                if not isinstance(value, param.type):
                    try:
                        # Try to cast the value
                        kwargs[param.name] = param.type(value)
                    except (ValueError, TypeError):
                        return False, f"Parameter '{param.name}' must be of type {param.type.__name__}"

        return True, None

    def get_info(self) -> Dict[str, Any]:
        """
        Get skill information.

        Returns:
            Dictionary containing skill metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type.__name__,
                    "required": p.required,
                    "description": p.description,
                    "default": p.default
                }
                for p in self.parameters
            ]
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class SkillRegistry:
    """
    Registry for managing available skills.
    """

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill):
        """
        Register a skill.

        Args:
            skill: Skill instance to register
        """
        self._skills[skill.name] = skill
        print(f"[SkillRegistry] Registered skill: {skill.name}")

    def unregister(self, skill_name: str):
        """
        Unregister a skill.

        Args:
            skill_name: Name of skill to unregister
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
            print(f"[SkillRegistry] Unregistered skill: {skill_name}")

    def get(self, skill_name: str) -> Optional[BaseSkill]:
        """
        Get a skill by name.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill instance or None if not found
        """
        return self._skills.get(skill_name)

    def list_skills(self) -> List[str]:
        """
        List all registered skill names.

        Returns:
            List of skill names
        """
        return list(self._skills.keys())

    def get_all_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered skills.

        Returns:
            Dictionary mapping skill names to their info
        """
        return {
            skill_name: skill.get_info()
            for skill_name, skill in self._skills.items()
        }

    def find_skills(self, keyword: str) -> List[str]:
        """
        Find skills matching a keyword.

        Args:
            keyword: Keyword to search for

        Returns:
            List of matching skill names
        """
        keyword_lower = keyword.lower()
        matching = []

        for skill_name, skill in self._skills.items():
            if (keyword_lower in skill_name.lower() or
                keyword_lower in skill.description.lower()):
                matching.append(skill_name)

        return matching


__all__ = [
    "BaseSkill",
    "SkillResult",
    "SkillParameter",
    "SkillRegistry"
]
