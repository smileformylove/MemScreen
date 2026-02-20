### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-02             ###
### license: MIT                 ###

"""
Input Classification Module.

This module provides intelligent classification of user inputs and queries
to optimize memory storage and retrieval.
"""

import json
import logging
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from .dynamic_models import (
    MemoryCategory,
    QueryIntent,
    ClassifiedInput,
    ClassifiedQuery,
)

logger = logging.getLogger(__name__)


class InputClassifier:
    """
    Classifier for categorizing user inputs and queries.

    Uses a combination of rule-based patterns and LLM-based classification
    to efficiently categorize inputs for optimized memory management.
    """

    # Pattern-based classification rules (fast path)
    PATTERNS = {
        MemoryCategory.QUESTION: [
            # English patterns
            r'^(what|how|why|when|where|who|which|can|could|would|should|is|are|do|does|did)\b',
            r'\?$',
            r'^tell me about',
            r'^explain',
            r'^define',
            # Chinese patterns
            r'^(|||||||||)\b',
            r'^(||||)\b',
            r'\?$',
            r'\?$',
            r'$',
        ],
        MemoryCategory.TASK: [
            # English patterns
            r'\b(todo|to-do|task|remember to|don\'t forget|need to|have to)\b',
            r'^\s*[-*+]\s',  # Bullet list items
            r'^\s*\d+\.\s',  # Numbered list items
            # Chinese patterns
            r'(||||||)',
            r'(.*|.*|.*|.*)',
            r'^\s*[-*+]\s',  # Bullet list items
            r'^\s*\d+[.]\s',  # Numbered list items
        ],
        MemoryCategory.CODE: [
            # Code patterns (language-agnostic)
            r'```',  # Code blocks
            r'\b(function|class|def|import|from|return|if __name__)\b',
            r'\b(var|let|const|function|=>|async|await)\b',
            # Chinese patterns
            r'(||||)',
        ],
        MemoryCategory.PROCEDURE: [
            # English patterns
            r'\b(step \d+|first|second|then|next|after that|finally)\b',
            r'\b(how to|how do i|instructions|guide|tutorial)\b',
            # Chinese patterns
            r'(|||||||)',
            r'(.*|.*|||)',
            r'(\s*\d+|.*)',
        ],
        MemoryCategory.GREETING: [
            # English patterns
            r'^(hi|hello|hey|good morning|good afternoon|good evening|greetings)',
            # Chinese patterns
            r'^(||||||)',
        ],
        MemoryCategory.DOCUMENT: [
            # English patterns
            r'\b(file|document|attachment|save|open|read)\b',
            r'\.(txt|md|pdf|doc|docx)\b',
            # Chinese patterns
            r'(|||||)',
        ],
        MemoryCategory.IMAGE: [
            # English patterns
            r'\b(image|screenshot|photo|picture|snapshot)\b',
            r'\.(png|jpg|jpeg|gif|bmp)\b',
            # Chinese patterns
            r'(||||)',
        ],
        MemoryCategory.PERSONAL: [
            # English patterns
            r'\b(my preference|i prefer|i like|i dislike|i want)\b',
            r'\b(remember that|i always|i usually)\b',
            # Chinese patterns
            r'(.*||||)',
            r'(.*||)',
        ],
        MemoryCategory.REFERENCE: [
            # English patterns
            r'https?://',  # URLs
            r'\b(link|reference|check out|see also)\b',
            # Chinese patterns
            r'(|||)',
        ],
        MemoryCategory.CONVERSATION: [
            # Chinese patterns for conversation
            r'(|||||)',
            r'(|)',
            r'(.*|.*)',
        ],
    }

    # Query intent patterns
    QUERY_PATTERNS = {
        QueryIntent.RETRIEVE_FACT: [
            # English patterns
            r'\b(what is|what are|tell me about|define|explain)\b',
            r'\b(remember|recall|lookup)\b',
            # Chinese patterns
            r'(||||)',
            r'(.*|.*|)',
        ],
        QueryIntent.FIND_PROCEDURE: [
            # English patterns
            r'\b(how to|how do i|how can i|steps for|instructions)\b',
            r'\b(guide|tutorial|walkthrough)\b',
            # Chinese patterns
            r'(.*|.*|.*||)',
            r'(||)',
        ],
        QueryIntent.SEARCH_CONVERSATION: [
            # English patterns
            r'\b(we talk(ed|ing)? about|you said|we discuss(ed|ing)?|mention(ed)?|said about)\b',
            r'\b(earlier|before|previously|last time|our conversation)\b',
            # Chinese patterns
            r'(|||||)',
            r'(||||)',
        ],
        QueryIntent.LOCATE_CODE: [
            # English patterns
            r'\b(code|function|class|implementation|script)\b',
            r'\b(show me the|find the|where is the)\s+(code|function|class)',
            # Chinese patterns
            r'(||||)',
            r'(||).*',
        ],
        QueryIntent.FIND_DOCUMENT: [
            # English patterns
            r'\b(document|file|note|saved)\b',
            r'\b(where did i|find the|locate the)\s+(document|file|note)',
            # Chinese patterns
            r'(|||)',
            r'(||).*(||)',
        ],
        QueryIntent.GET_TASKS: [
            # English patterns
            r'\b(todo|tasks|to-do|action items|what do i need to)\b',
            r'\b(what\'s next|what should i do|pending)\b',
            # Chinese patterns
            r'(|||)',
            r'(||)',
        ],
    }

    def __init__(self, llm=None, enable_llm_fallback: bool = True):
        """
        Initialize the input classifier.

        Args:
            llm: Language model for advanced classification
            enable_llm_fallback: Whether to use LLM for ambiguous inputs
        """
        self.llm = llm
        self.enable_llm_fallback = enable_llm_fallback

    def classify_input(
        self,
        text: str,
        use_llm: bool = False,
    ) -> ClassifiedInput:
        """
        Classify a user input into a memory category.

        Args:
            text: The input text to classify
            use_llm: Whether to use LLM for classification

        Returns:
            ClassifiedInput: The classification result
        """
        if not text or not text.strip():
            return ClassifiedInput(
                text=text,
                category=MemoryCategory.GENERAL,
                confidence=0.0,
            )

        text = text.strip()

        # Fast path: Pattern-based classification
        category, confidence = self._classify_by_patterns(text)

        # If low confidence and LLM is available, use LLM for better classification
        if confidence < 0.7 and use_llm and self.llm and self.enable_llm_fallback:
            llm_category, llm_confidence = self._classify_by_llm(text)
            if llm_confidence > confidence:
                category = llm_category
                confidence = llm_confidence

        # Extract additional metadata based on category
        metadata = self._extract_metadata(text, category)

        # Detect subcategories
        subcategories = self._detect_subcategories(text, category)

        return ClassifiedInput(
            text=text,
            category=category,
            confidence=confidence,
            subcategories=subcategories,
            metadata=metadata,
        )

    def classify_query(self, query: str) -> ClassifiedQuery:
        """
        Classify a search query to determine intent and target categories.

        Args:
            query: The search query

        Returns:
            ClassifiedQuery: The classification result
        """
        if not query or not query.strip():
            return ClassifiedQuery(
                query=query,
                intent=QueryIntent.GENERAL_SEARCH,
                target_categories=[MemoryCategory.GENERAL],
                confidence=0.0,
            )

        query = query.strip()

        # Detect intent from patterns
        intent = self._detect_query_intent(query)

        # Determine target categories based on intent
        target_categories = self._get_target_categories(intent, query)

        # Generate optimized search parameters
        search_params = self._generate_search_params(intent, target_categories)

        return ClassifiedQuery(
            query=query,
            intent=intent,
            target_categories=target_categories,
            confidence=0.9,  # High confidence for pattern matching
            search_params=search_params,
        )

    def _classify_by_patterns(self, text: str) -> Tuple[MemoryCategory, float]:
        """Classify using regex patterns (fast path)."""
        text_lower = text.lower()

        # Count matches for each category
        scores = {}
        for category, patterns in self.PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[category] = score

        if not scores:
            return MemoryCategory.GENERAL, 0.5

        # Return category with highest score
        best_category = max(scores, key=scores.get)
        confidence = min(0.9, 0.5 + scores[best_category] * 0.1)

        return best_category, confidence

    def _classify_by_llm(self, text: str) -> Tuple[MemoryCategory, float]:
        """Classify using LLM (fallback for ambiguous inputs)."""
        if not self.llm:
            return MemoryCategory.GENERAL, 0.5

        categories = [c.value for c in MemoryCategory]
        category_list = ", ".join(categories)

        prompt = f"""Classify the following text into one of these categories: {category_list}

Text: "{text}"

Respond with JSON in this format:
{{"category": "category_name", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

        try:
            response = self.llm.generate_response(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                options={"num_predict": 100, "temperature": 0.3},
            )

            result = json.loads(response)
            category = MemoryCategory(result.get("category", MemoryCategory.GENERAL))
            confidence = float(result.get("confidence", 0.7))

            return category, confidence

        except Exception as e:
            logger.warning(f"LLM classification failed: {e}, falling back to pattern matching")
            return self._classify_by_patterns(text)

    def _detect_query_intent(self, query: str) -> QueryIntent:
        """Detect the intent of a search query."""
        query_lower = query.lower()

        # Check each intent pattern
        for intent, patterns in self.QUERY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return intent

        return QueryIntent.GENERAL_SEARCH

    def _get_target_categories(
        self,
        intent: QueryIntent,
        query: str,
    ) -> List[MemoryCategory]:
        """Determine which categories to search based on intent."""
        intent_category_map = {
            QueryIntent.RETRIEVE_FACT: [
                MemoryCategory.FACT,
                MemoryCategory.CONCEPT,
                MemoryCategory.REFERENCE,
            ],
            QueryIntent.FIND_PROCEDURE: [
                MemoryCategory.PROCEDURE,
                MemoryCategory.WORKFLOW,
                MemoryCategory.TASK,
            ],
            QueryIntent.SEARCH_CONVERSATION: [
                MemoryCategory.CONVERSATION,
                MemoryCategory.GENERAL,
            ],
            QueryIntent.LOCATE_CODE: [
                MemoryCategory.CODE,
            ],
            QueryIntent.FIND_DOCUMENT: [
                MemoryCategory.DOCUMENT,
                MemoryCategory.REFERENCE,
            ],
            QueryIntent.GET_TASKS: [
                MemoryCategory.TASK,
                MemoryCategory.PROCEDURE,
            ],
            QueryIntent.GENERAL_SEARCH: [
                MemoryCategory.FACT,
                MemoryCategory.CONCEPT,
                MemoryCategory.CONVERSATION,
                MemoryCategory.GENERAL,
            ],
        }

        return intent_category_map.get(intent, [MemoryCategory.GENERAL])

    def _generate_search_params(
        self,
        intent: QueryIntent,
        categories: List[MemoryCategory],
    ) -> Dict[str, Any]:
        """Generate optimized search parameters based on intent and categories."""
        params = {
            "limit": 20,  # Default limit
            "min_score": 0.6,  # Default minimum score
        }

        # Adjust parameters based on intent
        if intent == QueryIntent.RETRIEVE_FACT:
            params["limit"] = 10
            params["min_score"] = 0.7  # Higher threshold for facts
        elif intent == QueryIntent.FIND_PROCEDURE:
            params["limit"] = 5  # Fewer, more relevant results
            params["min_score"] = 0.65
        elif intent == QueryIntent.LOCATE_CODE:
            params["limit"] = 10
            params["min_score"] = 0.7
        elif intent == QueryIntent.SEARCH_CONVERSATION:
            params["limit"] = 15  # More results for conversations
            params["min_score"] = 0.5  # Lower threshold for broader search

        return params

    def _extract_metadata(self, text: str, category: MemoryCategory) -> Dict[str, Any]:
        """Extract metadata based on category."""
        metadata = {}

        if category == MemoryCategory.TASK:
            # Extract priority and status
            if re.search(r'\b(urgent|important|asap|priority)\b', text, re.IGNORECASE):
                metadata["priority"] = "high"
            elif re.search(r'\b(low priority|when possible|eventually)\b', text, re.IGNORECASE):
                metadata["priority"] = "low"
            else:
                metadata["priority"] = "medium"

        elif category == MemoryCategory.CODE:
            # Detect programming language
            language_patterns = {
                "python": r'\b(def |import |from |print\(|if __name__)\b',
                "javascript": r'\b(const |let |var |function |=> |async |await )\b',
                "java": r'\b(public|private|protected|class|void|int|String)\b',
                "sql": r'\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\b',
            }
            for lang, pattern in language_patterns.items():
                if re.search(pattern, text, re.IGNORECASE):
                    metadata["language"] = lang
                    break

        elif category == MemoryCategory.REFERENCE:
            # Extract URLs
            urls = re.findall(r'https?://[^\s<>"]+', text)
            if urls:
                metadata["urls"] = urls

        return metadata

    def _detect_subcategories(self, text: str, category: MemoryCategory) -> List[str]:
        """Detect additional subcategories for more granular classification."""
        subcategories = []

        if category == MemoryCategory.QUESTION:
            if re.search(r'\b(why|because|reason)\b', text, re.IGNORECASE):
                subcategories.append("explanatory")
            if re.search(r'\b(how to|how do)\b', text, re.IGNORECASE):
                subcategories.append("procedural")
            if re.search(r'\b(what is|define|explain)\b', text, re.IGNORECASE):
                subcategories.append("definitional")

        elif category == MemoryCategory.TASK:
            if re.search(r'\b(recurring|daily|weekly|monthly)\b', text, re.IGNORECASE):
                subcategories.append("recurring")
            if re.search(r'\b(one-time|just this|single)\b', text, re.IGNORECASE):
                subcategories.append("one-time")

        return subcategories

    @lru_cache(maxsize=1000)
    def classify_cached(self, text: str) -> ClassifiedInput:
        """Cached version of classify_input for frequently used inputs."""
        return self.classify_input(text)


__all__ = ["InputClassifier"]
