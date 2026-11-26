"""
Генерация уникального номера заявки вида REQ-2026-000123.

Число берётся из последовательности PostgreSQL repair_request_number_seq
(создаётся миграцией). nextval() атомарна: даже при параллельном создании
заявок двумя пользователями каждый получит своё число — без блокировок
и без повторов при коллизии. UNIQUE на request_number — дополнительная страховка.
"""

from django.db import connection
from django.utils import timezone

SEQUENCE_NAME = "repair_request_number_seq"


def _format(year: int, value: int) -> str:
    return f"REQ-{year}-{value:06d}"


def generate_request_number() -> str:
    """Синхронная версия — для seed-команды, админки и синхронных вью."""
    with connection.cursor() as cur:
        cur.execute(f"SELECT nextval('{SEQUENCE_NAME}')")
        (value,) = cur.fetchone()
    return _format(timezone.localdate().year, value)


async def agenerate_request_number() -> str:
    """Асинхронная версия — для async-вью создания заявки."""
    from asgiref.sync import sync_to_async

    # Django не даёт асинхронного API для «сырого» SQL, поэтому запрос
    # выполняется в потоке через sync_to_async (так же устроен async ORM внутри).
    return await sync_to_async(generate_request_number, thread_sensitive=True)()
