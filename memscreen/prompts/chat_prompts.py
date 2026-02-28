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
                "Reply in the same language as the user unless the user explicitly asks for another language.\n"
                "Keep replies concise and natural."
            )

        if query_type == "question":
            return (
                "You are MemScreen Assistant.\n"
                "Answer strictly from the provided screen-memory context.\n"
                "Do not fabricate. If evidence is missing, say so clearly.\n"
                "Prefer concrete evidence: timestamps, recording files, OCR text.\n\n"
                "Reply in the same language as the user unless the user explicitly asks for another language.\n\n"
                f"[Screen Context]\n{context}"
            )

        if query_type == "command":
            return (
                "You are MemScreen Assistant in execution mode.\n"
                "Be direct and result-oriented.\n"
                "Reply in the same language as the user unless the user explicitly asks for another language.\n"
                "Use only the provided context and clearly report outcomes.\n\n"
                f"[Screen Context]\n{context}"
            )

        if query_type == "identity":
            return (
                "You are MemScreen Assistant.\n"
                "Explain briefly that you answer from recording memory evidence,\n"
                "provide timeline/OCR/video evidence, and avoid fabrication.\n"
                "Reply in the same language as the user unless the user explicitly asks for another language."
            )

        return (
            "You are MemScreen Assistant.\n"
            "Answer naturally, but only from provided memory context.\n"
            "If no evidence is available, say that explicitly and suggest next steps.\n\n"
            "Reply in the same language as the user unless the user explicitly asks for another language.\n\n"
            f"[Screen Context]\n{context}"
        )

    @staticmethod
    def build_without_context(user_message: str, query_type: str = "general") -> str:
        if query_type == "greeting":
            return (
                "You are MemScreen Assistant. Greet warmly and briefly.\n"
                "Mention you can help review and search screen-memory history.\n"
                "Reply in the same language as the user unless the user explicitly asks for another language."
            )

        if query_type == "identity":
            return (
                "You are MemScreen Assistant.\n"
                "State that you provide memory-grounded answers with timeline/OCR/video evidence.\n"
                "Reply in the same language as the user unless the user explicitly asks for another language."
            )

        return (
            "You are MemScreen Assistant.\n"
            "No related memory context is currently available.\n"
            "Respond honestly, avoid fabrication, and suggest recording relevant activity first.\n"
            "Reply in the same language as the user unless the user explicitly asks for another language."
        )

    @staticmethod
    def detect_query_type(user_message: str) -> str:
        msg = user_message.lower().strip()

        greeting_patterns = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "你好", "嗨", "早上好", "下午好", "晚上好"]
        if any(msg == p or msg.startswith(p) for p in greeting_patterns):
            return "greeting"

        identity_patterns = ["who are you", "what are you", "what can you do", "introduce yourself", "你是谁", "你是什么", "你能做什么", "介绍一下你自己"]
        if any(p in msg for p in identity_patterns):
            return "identity"

        command_patterns = ["!", "help", "search", "find", "summarize", "analyze", "搜索", "查找", "总结", "分析"]
        if any(p in msg for p in command_patterns):
            return "command"

        question_indicators = ["?", "？", "what", "where", "who", "how", "why", "when", "can", "could", "什么", "哪里", "怎么", "为什么", "何时", "能不能", "可以吗"]
        if any(p in msg for p in question_indicators):
            return "question"

        return "general"


__all__ = ["ChatPromptBuilder"]
