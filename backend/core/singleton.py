"""
Single shared LMStudioClient instance.
Import this module - never instantiate LMStudioClient elsewhere.
"""

from backend.config import settings
from backend.core.llm_client import LMStudioClient

llm = LMStudioClient(
    base_url=settings.lm_studio_url,
    model=settings.lm_studio_model,
    timeout=settings.lm_studio_timeout,
)
