from django.db import connection
from django.http import JsonResponse


def health(request):
    """Проверка работоспособности: подключение к БД и текущий уровень изоляции."""
    with connection.cursor() as cur:
        cur.execute("SELECT version(), current_setting('transaction_isolation')")
        version, isolation = cur.fetchone()
    return JsonResponse({"status": "ok", "database": version, "isolation_level": isolation})
