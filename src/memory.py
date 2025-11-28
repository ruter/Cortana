from zep_cloud.client import AsyncZep
from .config import config

# Global Zep client instance
memory_client = AsyncZep(api_key=config.ZEP_API_KEY)
