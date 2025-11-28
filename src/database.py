from supabase import create_client, Client
from .config import config

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        return cls._instance

    def get_client(self) -> Client:
        return self.client

# Global instance
db = Database().get_client()
