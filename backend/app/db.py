from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import MONGO_URI, MONGO_DB_NAME

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_client = Database()

async def connect_to_mongo():
    print(f"Connecting to MongoDB at {MONGO_URI.split('@')[-1] if '@' in MONGO_URI else MONGO_URI}...")
    db_client.client = AsyncIOMotorClient(MONGO_URI)
    db_client.db = db_client.client[MONGO_DB_NAME]
    print("Connected to MongoDB.")

async def close_mongo_connection():
    if db_client.client:
        db_client.client.close()
        print("MongoDB connection closed.")

def get_db():
    return db_client.db
