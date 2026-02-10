import os
from google import genai
from google.genai import types
from src.utils.logger import logger

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_response(prompt: str, temperature: float = 0.7) -> str:
    """
    Generate a response using Google Gemini LLM.
    
    Args:
        prompt: The input prompt for the LLM
        temperature: Sampling temperature (0.0 to 1.0)
        
    Returns:
        Generated text response
        
    Raises:
        Exception: If response generation fails
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=2048,
            )
        )
        logger.info("Successfully generated LLM response")
        return response.text
    except Exception as e:
        logger.error(f"Error generating LLM response: {str(e)}")
        raise


async def generate_structured_career_guidance(
    user_profile: str,
    career_context: str,
    prompt_template: str
) -> str:
    """
    Generate structured career guidance based on user profile and context.
    
    Args:
        user_profile: User's profile information
        career_context: Relevant career knowledge from vector DB
        prompt_template: Template for the prompt
        
    Returns:
        Structured career guidance response
    """
    prompt = prompt_template.format(
        user_profile=user_profile,
        career_context=career_context
    )
    
    return await generate_response(prompt, temperature=0.7)