"""Strands SDK configuration with Anthropic LLM backend."""

import json
from typing import Optional, Dict, Any, Type, TypeVar
from pydantic import BaseModel
from strands import Agent
from strands.models.anthropic import AnthropicModel
from src.core.config import get_settings
from src.core.logging import get_logger


logger = get_logger(__name__)
T = TypeVar('T', bound=BaseModel)


# Global Strands Agent instance
_strands_agent: Optional[Agent] = None


def initialize_llm() -> Agent:
    """Get or create the global Strands Agent instance."""
    global _strands_agent
    if _strands_agent is None:
        settings = get_settings()
        model = AnthropicModel(
            client_args={
                "api_key": settings.anthropic_api_key,
            },
            max_tokens=2048,
            model_id="claude-sonnet-4-20250514",
            params={
                "temperature": 0.7
            }
        )
        _strands_agent = Agent(model=model)
        logger.info("Strands Agent initialized with Anthropic Claude")
    return _strands_agent


async def shutdown_llm() -> None:
    """Cleanup Strands Agent during app shutdown."""
    global _strands_agent
    _strands_agent = None
    logger.info("Strands Agent shut down")


def generate_json(prompt: str, schema_class: Type[T]) -> T:
    """Generate JSON response from Anthropic Claude via Strands.
    
    Args:
        prompt: The prompt to send to Anthropic Claude
        schema_class: Pydantic model class to validate against
        
    Returns:
        Instance of schema_class with parsed data
        
    Raises:
        Exception: If JSON parsing fails or validation fails
    """
    agent = initialize_llm()
    
    try:
        # Call agent without structured_output - just get text response
        response = agent(prompt)
        
        
        if isinstance(response, str):
            response_text = response
        elif hasattr(response, 'response'):
            response_text = response.response
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            # Try to convert to string as fallback
            response_text = str(response)
        
        # Clean up markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed. Response text: {response_text}")
            raise Exception(f"Failed to parse JSON from Anthropic response: {str(e)}")
        
        # Validate and create Pydantic model instance
        try:
            return schema_class(**data)
        except Exception as e:
            logger.error(f"Schema validation failed. Data: {data}")
            raise Exception(f"Failed to validate response against schema: {str(e)}")
            
    except Exception as e:
        logger.error(f"generate_json failed: {str(e)}")
        raise
