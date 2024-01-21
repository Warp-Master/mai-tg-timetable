from os import getenv

from motor.motor_asyncio import AsyncIOMotorClient


mongo_client = AsyncIOMotorClient(getenv('MONGO_URI'))
db = mongo_client.db


async def init_db():
    collections = await db.list_collection_names()
    if 'access_log' not in collections:
        await db.create_collection(
            'access_log',
            timeseries={
                'timeField': 'ts',
                'metaField': 'handler',
            },
            expireAfterSeconds=0,
        )
