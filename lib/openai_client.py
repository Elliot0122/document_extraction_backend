import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion


class OpenAIClient:
    """Wrapper for OpenAI API operations."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.api_key)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        """Generate a chat completion using OpenAI's API.

        Args:
            messages: List of message objects with role and content.
            model: The model to use for completion.
            temperature: Controls randomness. Higher values mean more random.
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The API response as a ChatCompletion object.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response
        except Exception as e:
            raise

    def extract_completion_text(self, completion_response: ChatCompletion) -> str:
        """Extract the text from a completion response.

        Args:
            completion_response: The response from a chat completion call.

        Returns:
            The extracted text content from the response.
        """
        if hasattr(completion_response, "choices") and len(completion_response.choices) > 0:
            return completion_response.choices[0].message.content or ""
        return ""

    def generate_tick_marking_question(
        self,
        user_query: str,
        model: str = "gpt-4o-mini",
    ) -> str:
        """Generate a concise question that asks about the following thing: {user_query}

        Args:
            user_query: The user's query.

        Returns:
            A question that asks about {user_query}
        """
        
        prompt = f'''
        Generate a question that asks for "{user_query}". 
        For example, the question for "ticket creation time" is "When is the ticket created?" 
        and the question for "ticket creator" is "Who created this ticket?"
        '''
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates concise questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()