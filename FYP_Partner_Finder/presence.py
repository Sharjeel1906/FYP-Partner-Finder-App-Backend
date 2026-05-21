from django.core.cache import cache

from .models import UserProfile


def _connection_key(user_id):
    return f"ws_connections:{user_id}"


def mark_user_connected(user_id):
    key = _connection_key(user_id)
    count = cache.get(key, 0) + 1
    cache.set(key, count, timeout=86400)
    if count == 1:
        UserProfile.objects.filter(user_id=user_id).update(is_online=True)


def mark_user_disconnected(user_id):
    key = _connection_key(user_id)
    count = max(0, cache.get(key, 0) - 1)
    if count == 0:
        cache.delete(key)
        UserProfile.objects.filter(user_id=user_id).update(is_online=False)
    else:
        cache.set(key, count, timeout=86400)
