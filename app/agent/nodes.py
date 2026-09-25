"""Nodes for the agentic RAG workflow."""

from app.agent.llm.base import LLMProvider
from app.agent.state import AgentState
from app.retrieval.retriever import SemanticRetriever


class AgentNodes:
    """Implement the individual nodes used by the agentic RAG workflow."""

    def __init__(
        self,
        retriever: SemanticRetriever,
        llm_provider: LLMProvider,
        *,
        openai_provider: LLMProvider | None = None,
        gemini_provider: LLMProvider | None = None,
        max_retrieval_attempts: int = 2,
    ) -> None:
        """Initialize agent nodes."""
        if max_retrieval_attempts <= 0:
            raise ValueError("max_retrieval_attempts must be greater than zero")

        self._retriever = retriever
        self._llm_provider = llm_provider
        self._openai_provider = openai_provider
        self._gemini_provider = gemini_provider
        self._max_retrieval_attempts = max_retrieval_attempts

    def planner(self, state: AgentState) -> AgentState:
        """Validate the query and prepare the state for retrieval."""
        query = state.query.strip()
        user_id = state.user_id.strip()

        if not query:
            raise ValueError("query cannot be empty")

        if not user_id:
            raise ValueError("user_id cannot be empty")

        state.query = query
        state.user_id = user_id

        return state

    def retrieve(self, state: AgentState) -> AgentState:
        """Retrieve relevant chunks for the current user's query."""
        if state.retrieval_attempts >= self._max_retrieval_attempts:
            state.error = "Maximum retrieval attempts reached."
            return state

        results = self._retriever.retrieve(
            query=state.query,
            user_id=state.user_id,
            document_id=state.document_id,
            top_k=5,
        )

        state.retrieved_chunks = [
            {
                "chunk_id": result.chunk_id,
                "text": result.text,
                "metadata": result.metadata,
            }
            for result in results
        ]

        state.retrieval_attempts += 1

        return state

    def generate(self, state: AgentState) -> AgentState:
        """Generate answers using the available language model providers."""
        if not state.retrieved_chunks:
            state.answer = (
                "I could not find relevant information in your documents "
                "to answer this question."
            )
            return state

        context_parts = [
            chunk["text"] for chunk in state.retrieved_chunks if chunk.get("text")
        ]

        if not context_parts:
            state.answer = (
                "I could not find relevant information in your documents "
                "to answer this question."
            )
            return state

        context = "\n\n".join(context_parts)

        system_prompt = (
            "You are a document question-answering assistant. "
            "Answer the user's question using only the provided document "
            "context. Use the conversation history to understand references "
            "and follow-up questions. Do not invent information."
        )

        history = self._format_conversation_history(state)

        user_prompt = (
            f"Conversation history:\n{history}\n\n"
            f"Question:\n{state.query}\n\n"
            f"Document context:\n{context}"
        )

        # Production mode: use both OpenAI and Gemini.
        if self._openai_provider is not None and self._gemini_provider is not None:
            state.openai_answer = self._openai_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            state.gemini_answer = self._gemini_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            state.answer = self._combine_provider_answers(
                state.openai_answer,
                state.gemini_answer,
            )

            return state

        # Test/backward-compatible mode: use the existing provider.
        state.answer = self._llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return state

    @staticmethod
    def _combine_provider_answers(
        openai_answer: str,
        gemini_answer: str,
    ) -> str:
        """Combine the two provider responses into a transparent answer."""
        return (
            "OpenAI answer:\n"
            f"{openai_answer}\n\n"
            "Gemini answer:\n"
            f"{gemini_answer}"
        )

    @staticmethod
    def _format_conversation_history(
        state: AgentState,
    ) -> str:
        """Format previous conversation messages for the LLM."""
        if not state.conversation_history:
            return "No previous conversation."

        return "\n".join(
            f"{message.role.capitalize()}: {message.content}"
            for message in state.conversation_history
        )

    def verify(self, state: AgentState) -> AgentState:
        """Verify that an answer has supporting retrieved context."""
        if not state.answer:
            state.verification_passed = False
            state.verification_reason = "No answer was generated."
            return state

        if not state.retrieved_chunks:
            state.verification_passed = False
            state.verification_reason = "No supporting documents were retrieved."
            return state

        context = " ".join(
            chunk["text"] for chunk in state.retrieved_chunks if chunk.get("text")
        )

        if not context.strip():
            state.verification_passed = False
            state.verification_reason = "Retrieved chunks contain no text."
            return state

        state.verification_passed = True
        state.verification_reason = "Answer has supporting retrieved context."

        return state