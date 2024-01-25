import pymongo
from django.conf import settings

from audojiengine.logging_config import configure_logger

logger = configure_logger(__name__)

# Initialize a MongoDB client
client = pymongo.MongoClient(settings.MONGO_DB_URL)
db = client[settings.MONGO_DB_NAME]


async def store_data_to_audio_segment_mgdb(segment_data):
    try:
        # # Replace 'your_collection_name' with your actual collection name
        # collection = db["your_collection_name"]
        # # Insert the document into MongoDB
        # collection.insert_one(segment_data)
        logger.info("Data stored in MongoDB successfully.")
    except pymongo.errors.PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


async def store_data_to_audio_mgdb(segment_data):
    try:
        #     # Replace 'your_collection_name' with your actual collection name
        #     collection = db["your_collection_name"]
        #     # Insert the document into MongoDB
        #     collection.insert_one(segment_data)
        logger.info("Data stored in MongoDB successfully.")
    except pymongo.errors.PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
