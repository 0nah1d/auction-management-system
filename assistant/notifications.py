import redis
from django.conf import settings


def publish_notification(channel, message):
    # Connect to Redis
    redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

    # Publish the message to the specified channel
    redis_client.publish(channel, message)
