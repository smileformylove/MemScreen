### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

"""
Search Memory Skill - Searches through user's screen memory
"""

from typing import Dict, Any
from ...agent.base_skill import BaseSkill, SkillResult, SkillParameter


class SearchMemorySkill(BaseSkill):
    """
    Skill for searching through the user's screen memory.

    This skill searches for relevant information in the user's screen recordings,
    OCR text, and other stored memories.
    """

    name = "search_memory"
    description = "Search through the user's screen memory for relevant information"
    version = "1.0.0"

    parameters = [
        SkillParameter(
            name="query",
            type=str,
            required=True,
            description="The search query to look for in memory"
        ),
        SkillParameter(
            name="top_k",
            type=int,
            required=False,
            description="Number of results to return",
            default=5
        ),
        SkillParameter(
            name="user_id",
            type=str,
            required=False,
            description="User ID to search memories for",
            default="screenshot"
        )
    ]

    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the memory search.

        Args:
            query: Search query
            top_k: Number of results
            user_id: User ID

        Returns:
            SkillResult with search results
        """
        import time
        start_time = time.time()

        try:
            query = kwargs.get("query")
            top_k = kwargs.get("top_k", 5)
            user_id = kwargs.get("user_id", "screenshot")

            if not query:
                return SkillResult(
                    success=False,
                    data=None,
                    error="Query parameter is required"
                )

            # Search in memory system
            if self.memory_system and hasattr(self.memory_system, 'search'):
                results = self.memory_system.search(
                    query=query,
                    user_id=user_id,
                    top_k=top_k
                )

                # Extract relevant information
                if results and 'results' in results:
                    search_results = results['results'][:top_k]

                    # Format results
                    formatted_results = []
                    for result in search_results:
                        formatted_results.append({
                            "content": result.get('document', ''),
                            "metadata": result.get('metadata', {}),
                            "score": result.get('score', 0.0)
                        })

                    return SkillResult(
                        success=True,
                        data={
                            "query": query,
                            "results": formatted_results,
                            "count": len(formatted_results)
                        },
                        metadata={
                            "search_method": "semantic_search",
                            "top_k": top_k
                        },
                        execution_time=time.time() - start_time
                    )
                else:
                    return SkillResult(
                        success=True,
                        data={
                            "query": query,
                            "results": [],
                            "count": 0
                        },
                        metadata={"message": "No results found"},
                        execution_time=time.time() - start_time
                    )
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    error="Memory system not available"
                )

        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Search failed: {str(e)}",
                execution_time=time.time() - start_time
            )


__all__ = ["SearchMemorySkill"]
