from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """
    Стандартный обработчик DRF + понятный ответ при попытке удалить запись,
    на которую ссылаются другие (FK с on_delete=PROTECT).
    """
    if isinstance(exc, ProtectedError):
        related = sorted({obj._meta.verbose_name_plural.lower() for obj in exc.protected_objects})
        return Response(
            {"detail": "Нельзя удалить: запись используется (" + ", ".join(related) + ")."},
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
