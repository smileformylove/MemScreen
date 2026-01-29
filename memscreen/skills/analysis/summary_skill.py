### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

"""
Summary Skill - Summarizes content using LLM
"""

from typing import Dict, Any
from ...agent.base_skill import BaseSkill, SkillResult, SkillParameter


class SummarySkill(BaseSkill):
    """
    Skill for summarizing content using LLM.

    This skill can summarize various types of content including
    search results, screen recordings, and conversations.
    """

    name = "summarize"
    description = "Summarize content using AI language models"
    version = "1.0.0"

    parameters = [
        SkillParameter(
            name="content",
            type=str,
            required=True,
            description="Content to summarize"
        ),
        SkillParameter(
            name="max_length",
            type=int,
            required=False,
            description="Maximum length of summary in characters",
            default=500
        ),
        SkillParameter(
            name="style",
            type=str,
            required=False,
            description="Summary style (brief, detailed, bullet_points)",
            default="brief"
        )
    ]

    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the summary generation.

        Args:
            content: Content to summarize
            max_length: Maximum length
            style: Summary style

        Returns:
            SkillResult with generated summary
        """
        import time
        start_time = time.time()

        try:
            content = kwargs.get("content")
            max_length = kwargs.get("max_length", 500)
            style = kwargs.get("style", "brief")

            if not content:
                return SkillResult(
                    success=False,
                    data=None,
                    error="Content parameter is required"
                )

            # Build summary prompt
            prompt = self._build_summary_prompt(content, max_length, style)

            # Generate summary using LLM
            if self.llm_client:
                summary = await self._generate_summary(prompt)
            else:
                # Fallback: simple truncation
                summary = content[:max_length]
                if len(content) > max_length:
                    summary += "..."

            return SkillResult(
                success=True,
                data={
                    "summary": summary,
                    "original_length": len(content),
                    "summary_length": len(summary),
                    "style": style
                },
                metadata={
                    "method": "llm" if self.llm_client else "truncation",
                    "max_length": max_length
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Summary generation failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def _build_summary_prompt(self, content: str, max_length: int, style: str) -> str:
        """Build prompt for LLM summary generation."""

        style_instructions = {
            "brief": "Provide a concise 2-3 sentence summary.",
            "detailed": "Provide a comprehensive summary covering all key points.",
            "bullet_points": "Provide a bulleted list of key points."
        }

        instruction = style_instructions.get(style, style_instructions["brief"])

        prompt = f"""请总结以下内容：

{instruction}

最多 {max_length} 个字符。

内容：
{content}

总结："""

        return prompt

    async def _generate_summary(self, prompt: str) -> str:
        """Generate summary using LLM."""
        try:
            if hasattr(self.llm_client, 'generate_response'):
                response = self.llm_client.generate_response(
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.strip()
            elif hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.strip()
            else:
                return str(self.llm_client)
        except Exception as e:
            print(f"[SummarySkill] LLM generation failed: {e}")
            raise


__all__ = ["SummarySkill"]
