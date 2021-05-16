import redis
import sys
import os
from dotenv import load_dotenv

# Export environment variables from .env file
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")


def redis_connect() -> redis.client.Redis:
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            socket_timeout=5,
        )
        ping = client.ping()
        if ping is True:
            return client
    except redis.AuthenticationError:
        print("Redis AuthenticationError")
        sys.exit(1)
