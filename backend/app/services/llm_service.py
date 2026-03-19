from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from typing import List, Dict, Any, AsyncGenerator, Optional
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger()


def _build_human_content(text: str, image_base64: Optional[str] = None) -> Any:
    """텍스트 + 이미지(base64)를 HumanMessage content로 변환 (GPT-4o Vision)"""
    if not image_base64:
        return text
    content: list = [{"type": "text", "text": text}]
    if image_base64.startswith("data:"):
        url = image_base64
    else:
        url = f"data:image/jpeg;base64,{image_base64}"
    content.append({"type": "image_url", "image_url": {"url": url}})
    return content


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
            streaming=True,
            max_tokens=1000,
            request_timeout=60,
        )

        self.llm_non_streaming = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
            streaming=False,
            max_tokens=1000,
            request_timeout=60,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        image_base64: Optional[str] = None,
    ) -> str:
        """Generate a non-streaming response from the LLM."""
        try:
            messages = [SystemMessage(content=system_prompt)]

            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=_build_human_content(user_message, image_base64)))

            response = await self.llm_non_streaming.agenerate([messages])
            return response.generations[0][0].text

        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_streaming_response(
        self,
        system_prompt: str,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        image_base64: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM."""
        try:
            messages = [SystemMessage(content=system_prompt)]

            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=_build_human_content(user_message, image_base64)))

            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content

        except Exception as e:
            logger.error(f"Error generating streaming LLM response: {str(e)}")
            raise

    async def check_hallucination(self, context: str, answer: str) -> Dict[str, Any]:
        """
        Check if the answer is grounded in the provided context.
        Returns a dict with 'is_grounded' boolean and 'explanation'.
        """
        try:
            from app.core.prompts import HALLUCINATION_CHECK_PROMPT
            
            prompt = HALLUCINATION_CHECK_PROMPT.format(
                context=context,
                answer=answer,
            )
            
            response = await self.generate_response(
                system_prompt="You are an expert at evaluating factual accuracy.",
                user_message=prompt,
            )
            
            is_grounded = response.lower().startswith("yes")
            
            return {
                "is_grounded": is_grounded,
                "explanation": response,
            }

        except Exception as e:
            logger.error(f"Error checking hallucination: {str(e)}")
            return {
                "is_grounded": True,
                "explanation": "Unable to verify",
            }

    async def expand_query(self, query: str) -> List[str]:
        """
        Expand the query with related keywords and synonyms.
        Useful for improving search recall.
        """
        try:
            from app.core.prompts import QUERY_EXPANSION_PROMPT
            
            prompt = QUERY_EXPANSION_PROMPT.format(question=query)
            
            response = await self.generate_response(
                system_prompt="You are a helpful assistant that generates related keywords.",
                user_message=prompt,
            )
            
            keywords = [kw.strip() for kw in response.split(",")]
            return keywords

        except Exception as e:
            logger.error(f"Error expanding query: {str(e)}")
            return [query]

    async def generate_conversation_title(self, first_message: str) -> str:
        """
        Generate a short, descriptive title for a conversation based on the first message.
        Uses GPT-4o-mini for fast, cost-effective title generation.
        """
        try:
            llm_mini = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.3,
                max_tokens=50,
            )
            
            system_prompt = "You are a helpful assistant that creates short, descriptive titles for conversations. Generate a title in 5 words or less that captures the main topic of the user's message. Respond ONLY with the title, no additional text."
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Create a short title for this conversation starter:\n\n{first_message}")
            ]
            
            response = await llm_mini.agenerate([messages])
            title = response.generations[0][0].text.strip()
            
            if len(title) > 100:
                title = title[:97] + "..."
            
            return title

        except Exception as e:
            logger.error(f"Error generating conversation title: {str(e)}")
            return first_message[:50] + "..." if len(first_message) > 50 else first_message
