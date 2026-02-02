"""
Dynamic Memory System Tests.

Tests for the dynamic memory classification and retrieval features.
"""

import pytest
from memscreen.memory import (
    MemoryCategory,
    QueryIntent,
    ClassifiedInput,
    ClassifiedQuery,
    DynamicMemoryConfig,
    InputClassifier,
)


class TestInputClassifier:
    """Tests for the InputClassifier class."""

    def test_classify_question(self):
        """Test classification of questions."""
        classifier = InputClassifier()

        # Question patterns
        questions = [
            "What is the capital of France?",
            "How do I create a Python function?",
            "Why does my code keep failing?",
            "When is the project deadline?",
        ]

        for question in questions:
            result = classifier.classify_input(question)
            assert result.category == MemoryCategory.QUESTION
            assert result.confidence > 0.5

    def test_classify_task(self):
        """Test classification of tasks."""
        classifier = InputClassifier()

        # Task patterns
        tasks = [
            "Remember to call the client tomorrow",
            "I need to finish the report by Friday",
            "Todo: Review the pull request",
        ]

        for task in tasks:
            result = classifier.classify_input(task)
            assert result.category == MemoryCategory.TASK
            assert result.confidence > 0.5

    def test_classify_code(self):
        """Test classification of code."""
        classifier = InputClassifier()

        # Code patterns
        code_snippets = [
            "def hello_world():\n    print('Hello')",
            "```python\nimport numpy as np\n```",
            "const add = (a, b) => a + b;",
        ]

        for code in code_snippets:
            result = classifier.classify_input(code)
            assert result.category == MemoryCategory.CODE
            assert result.confidence > 0.5

    def test_classify_procedure(self):
        """Test classification of procedures."""
        classifier = InputClassifier()

        # Procedure patterns
        procedures = [
            "Step 1: Install dependencies\nStep 2: Run the server",
            "How to deploy the application: First, build the Docker image...",
            "Instructions for setting up the database",
        ]

        for procedure in procedures:
            result = classifier.classify_input(procedure)
            assert result.category == MemoryCategory.PROCEDURE
            assert result.confidence > 0.5

    def test_classify_greeting(self):
        """Test classification of greetings."""
        classifier = InputClassifier()

        # Greeting patterns
        greetings = [
            "Hello there!",
            "Hi, how are you?",
            "Good morning!",
        ]

        for greeting in greetings:
            result = classifier.classify_input(greeting)
            assert result.category == MemoryCategory.GREETING
            assert result.confidence > 0.5

    def test_classify_query_intent_fact(self):
        """Test query intent classification for facts."""
        classifier = InputClassifier()

        queries = [
            "What is the HTTP protocol?",
            "Tell me about machine learning",
            "Define REST API",
        ]

        for query in queries:
            result = classifier.classify_query(query)
            assert result.intent == QueryIntent.RETRIEVE_FACT

    def test_classify_query_intent_procedure(self):
        """Test query intent classification for procedures."""
        classifier = InputClassifier()

        queries = [
            "How to create a virtual environment?",
            "How do I reset my password?",
            "Steps for configuring the server",
        ]

        for query in queries:
            result = classifier.classify_query(query)
            assert result.intent == QueryIntent.FIND_PROCEDURE

    def test_classify_query_intent_conversation(self):
        """Test query intent classification for conversations."""
        classifier = InputClassifier()

        queries = [
            "What did we discuss about the project?",
            "We talked about this earlier",
            "What was my previous question about X?",
        ]

        for query in queries:
            result = classifier.classify_query(query)
            assert result.intent == QueryIntent.SEARCH_CONVERSATION


class TestDynamicMemoryConfig:
    """Tests for DynamicMemoryConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = DynamicMemoryConfig()

        assert config.enable_auto_classification is True
        assert config.enable_intent_classification is True
        assert config.use_category_collections is True
        assert config.enable_category_weights is True

    def test_custom_weights(self):
        """Test custom category weights."""
        config = DynamicMemoryConfig(
            default_category_weights={
                MemoryCategory.TASK: 2.0,
                MemoryCategory.FACT: 1.5,
            }
        )

        assert config.default_category_weights[MemoryCategory.TASK] == 2.0
        assert config.default_category_weights[MemoryCategory.FACT] == 1.5


class TestMemoryCategory:
    """Tests for MemoryCategory enum."""

    def test_all_categories(self):
        """Test all category values exist."""
        categories = [
            MemoryCategory.QUESTION,
            MemoryCategory.TASK,
            MemoryCategory.FACT,
            MemoryCategory.CONCEPT,
            MemoryCategory.CONVERSATION,
            MemoryCategory.GREETING,
            MemoryCategory.CODE,
            MemoryCategory.DOCUMENT,
            MemoryCategory.IMAGE,
            MemoryCategory.VIDEO,
            MemoryCategory.PROCEDURE,
            MemoryCategory.WORKFLOW,
            MemoryCategory.PERSONAL,
            MemoryCategory.REFERENCE,
            MemoryCategory.GENERAL,
        ]

        assert len(categories) == 15

    def test_category_values(self):
        """Test category string values."""
        assert MemoryCategory.QUESTION.value == "question"
        assert MemoryCategory.TASK.value == "task"
        assert MemoryCategory.FACT.value == "fact"


class TestQueryIntent:
    """Tests for QueryIntent enum."""

    def test_all_intents(self):
        """Test all intent values exist."""
        intents = [
            QueryIntent.RETRIEVE_FACT,
            QueryIntent.FIND_PROCEDURE,
            QueryIntent.SEARCH_CONVERSATION,
            QueryIntent.LOCATE_CODE,
            QueryIntent.FIND_DOCUMENT,
            QueryIntent.GET_TASKS,
            QueryIntent.GENERAL_SEARCH,
        ]

        assert len(intents) == 7

    def test_intent_values(self):
        """Test intent string values."""
        assert QueryIntent.RETRIEVE_FACT.value == "retrieve_fact"
        assert QueryIntent.FIND_PROCEDURE.value == "find_procedure"


class TestClassifiedInput:
    """Tests for ClassifiedInput model."""

    def test_classification_result(self):
        """Test classification result structure."""
        result = ClassifiedInput(
            text="What is Python?",
            category=MemoryCategory.QUESTION,
            confidence=0.95,
            subcategories=["definitional"],
            metadata={"language": "en"},
        )

        assert result.text == "What is Python?"
        assert result.category == MemoryCategory.QUESTION
        assert result.confidence == 0.95
        assert result.subcategories == ["definitional"]
        assert result.metadata == {"language": "en"}


class TestClassifiedQuery:
    """Tests for ClassifiedQuery model."""

    def test_query_classification_result(self):
        """Test query classification result structure."""
        result = ClassifiedQuery(
            query="How to create a function?",
            intent=QueryIntent.FIND_PROCEDURE,
            target_categories=[MemoryCategory.PROCEDURE, MemoryCategory.CODE],
            confidence=0.9,
            search_params={"limit": 5, "min_score": 0.65},
        )

        assert result.query == "How to create a function?"
        assert result.intent == QueryIntent.FIND_PROCEDURE
        assert len(result.target_categories) == 2
        assert result.confidence == 0.9
        assert result.search_params["limit"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
