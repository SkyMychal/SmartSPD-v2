"""
AI Service abstraction layer for OpenAI and Azure OpenAI
"""
import openai
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

from app.core.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    OPENAI = "openai"
    AZURE = "azure"

@dataclass
class AIResponse:
    """Standardized AI response format"""
    content: str
    token_count: int
    model: str
    provider: str
    finish_reason: Optional[str] = None

class AIService:
    """Unified AI service supporting both OpenAI and Azure OpenAI"""
    
    def __init__(self):
        self.provider = AIProvider(settings.AI_SERVICE_PROVIDER.lower())
        self._setup_client()
    
    def _setup_client(self):
        """Setup the appropriate AI client"""
        if self.provider == AIProvider.AZURE:
            if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
                raise AIServiceError("Azure OpenAI credentials not configured", "AZURE_SETUP")
            
            openai.api_type = "azure"
            openai.api_base = settings.AZURE_OPENAI_ENDPOINT
            openai.api_key = settings.AZURE_OPENAI_API_KEY
            openai.api_version = settings.AZURE_OPENAI_API_VERSION
            
            logger.info("Initialized Azure OpenAI client")
            
        else:  # OpenAI
            if not settings.OPENAI_API_KEY:
                raise AIServiceError("OpenAI API key not configured", "OPENAI_SETUP")
            
            openai.api_type = "open_ai"
            openai.api_key = settings.OPENAI_API_KEY
            
            logger.info("Initialized OpenAI client")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.2,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion with provider abstraction"""
        
        try:
            # Determine the model to use
            if not model:
                model = self._get_default_chat_model()
            elif self.provider == AIProvider.AZURE:
                model = self._map_to_azure_deployment(model)
            
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                token_count=response.usage.total_tokens if response.usage else 0,
                model=model,
                provider=self.provider.value,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise AIServiceError(f"Chat completion failed: {e}", self.provider.value)
    
    async def create_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Create text embedding with provider abstraction"""
        
        try:
            if not model:
                model = self._get_default_embedding_model()
            elif self.provider == AIProvider.AZURE:
                model = self._map_to_azure_deployment(model, "embedding")
            
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(
                input=text,
                model=model
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            raise AIServiceError(f"Embedding creation failed: {e}", self.provider.value)
    
    def _get_default_chat_model(self) -> str:
        """Get default chat model for the provider"""
        if self.provider == AIProvider.AZURE:
            return settings.AZURE_OPENAI_GPT4_DEPLOYMENT
        else:
            return "gpt-4"
    
    def _get_default_embedding_model(self) -> str:
        """Get default embedding model for the provider"""
        if self.provider == AIProvider.AZURE:
            return settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        else:
            return "text-embedding-ada-002"
    
    def _map_to_azure_deployment(self, model: str, model_type: str = "chat") -> str:
        """Map OpenAI model names to Azure deployment names"""
        if self.provider != AIProvider.AZURE:
            return model
        
        # Chat model mappings
        if model_type == "chat":
            if model.startswith("gpt-4"):
                return settings.AZURE_OPENAI_GPT4_DEPLOYMENT
            elif model.startswith("gpt-3.5"):
                return settings.AZURE_OPENAI_GPT35_DEPLOYMENT
            else:
                return settings.AZURE_OPENAI_GPT4_DEPLOYMENT  # Default to GPT-4
        
        # Embedding model mappings
        elif model_type == "embedding":
            return settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        
        return model
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider"""
        info = {
            "provider": self.provider.value,
            "initialized": True
        }
        
        if self.provider == AIProvider.AZURE:
            info.update({
                "endpoint": settings.AZURE_OPENAI_ENDPOINT,
                "api_version": settings.AZURE_OPENAI_API_VERSION,
                "gpt4_deployment": settings.AZURE_OPENAI_GPT4_DEPLOYMENT,
                "gpt35_deployment": settings.AZURE_OPENAI_GPT35_DEPLOYMENT,
                "embedding_deployment": settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            })
        
        return info
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the AI service connection"""
        try:
            test_response = await self.chat_completion(
                messages=[{"role": "user", "content": "Hello, this is a connection test."}],
                max_tokens=10
            )
            
            return {
                "status": "connected",
                "provider": self.provider.value,
                "model": test_response.model,
                "token_count": test_response.token_count
            }
            
        except Exception as e:
            logger.error(f"AI service connection test failed: {e}")
            return {
                "status": "failed",
                "provider": self.provider.value,
                "error": str(e)
            }

# Global AI service instance
ai_service = AIService()