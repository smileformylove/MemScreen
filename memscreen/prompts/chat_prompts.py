"""Chat prompt templates for MemScreen."""


class ChatPromptBuilder:
    """Build context-aware system prompts for chat responses."""

    @staticmethod
    def build_with_context(context: str, user_message: str, query_type: str = "general") -> str:
        if not context:
            return ChatPromptBuilder.build_without_context(user_message, query_type)

        if query_type == "greeting":
            return (
                "You are MemScreen Assistant. Respond warmly and briefly.\n"
                "You can answer based on screen-memory evidence.\n"
                "Keep replies concise and natural."
            )

        if query_type == "question":
            return (
                "You are MemScreen Assistant.\n"
                "Answer strictly from the provided screen-memory context.\n"
                "Do not fabricate. If evidence is missing, say so clearly.\n"
                "Prefer concrete evidence: timestamps, recording files, OCR text.\n\n"
                f"[Screen Context]\n{context}"
            )

        if query_type == "command":
            return (
                "You are MemScreen Assistant in execution mode.\n"
                "Be direct and result-oriented.\n"
                "Use only the provided context and clearly report outcomes.\n\n"
                f"[Screen Context]\n{context}"
            )

        if query_type == "identity":
            return (
                "You are MemScreen Assistant.\n"
                "Explain briefly that you answer from recording memory evidence,\n"
                "provide timeline/OCR/video evidence, and avoid fabrication."
            )

        return (
            "You are MemScreen Assistant.\n"
            "Answer naturally, but only from provided memory context.\n"
            "If no evidence is available, say that explicitly and suggest next steps.\n\n"
            f"[Screen Context]\n{context}"
        )

    @staticmethod
    def build_without_context(user_message: str, query_type: str = "general") -> str:
        if query_type == "greeting":
            return (
                "You are MemScreen Assistant. Greet warmly and briefly.\n"
                "Mention you can help review and search screen-memory history."
            )

        if query_type == "identity":
            return (
                "You are MemScreen Assistant.\n"
                "State that you provide memory-grounded answers with timeline/OCR/video evidence."
            )

        return (
            "You are MemScreen Assistant.\n"
            "No related memory context is currently available.\n"
            "Respond honestly, avoid fabrication, and suggest recording relevant activity first."
        )

    @staticmethod
    def detect_query_type(user_message: str) -> str:
        msg = user_message.lower().strip()

        greeting_patterns = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        if any(msg == p or msg.startswith(p) for p in greeting_patterns):
            return "greeting"

        identity_patterns = ["who are you", "what are you", "what can you do", "introduce yourself"]
        if any(p in msg for p in identity_patterns):
            return "identity"

        command_patterns = ["!", "help", "search", "find", "summarize", "analyze"]
        if any(p in msg for p in command_patterns):
            return "command"

        question_indicators = ["?", "what", "where", "who", "how", "why", "when", "can", "could"]
        if any(p in msg for p in question_indicators):
            return "question"

        return "general"


__all__ = ["ChatPromptBuilder"]
