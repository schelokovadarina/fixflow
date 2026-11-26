"""
Асинхронное обращение к БД (п. 3.3 задания): чтение и добавление заявок.

Это обычные async-вью Django (DRF асинхронные вью не поддерживает).
Запросы к БД выполняются асинхронным ORM:
  * async for ... in queryset  — асинхронная итерация (чтение);
  * aexists(), aget(), acreate() — асинхронные проверка, выборка, вставка.

Пока запрос ждёт ответа PostgreSQL, рабочий процесс (ASGI-сервер uvicorn)
не блокируется и обслуживает другие запросы.

ВАЖНО: блокировки строк (select_for_update) здесь НЕ используются — асинхронный
ORM и блокировки вместе работают ненадёжно. Операции изменения с блокировками
вынесены в синхронные функции (services.py, этап 4).
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.catalog.models import Equipment, RequestStatus
from apps.staff.models import Employee

from .models import RepairRequest
from .numbering import agenerate_request_number
from .serializers import RepairRequestListSerializer
from .views import REQUEST_SELECT_RELATED

JSON_PARAMS = {"ensure_ascii": False}  # кириллица в ответе без \u-экранирования


def serialize(req: RepairRequest) -> dict:
    # Сериализатор берёт данные только из уже загруженных связанных объектов
    # (select_related), поэтому дополнительных — синхронных — запросов к БД не делает.
    return RepairRequestListSerializer(req).data


@require_GET
async def list_active_requests(request):
    """
    GET /api/requests/active/?limit=30
    Активные (незакрытые) заявки, сначала новые. Асинхронное ЧТЕНИЕ.
    """
    try:
        limit = min(max(int(request.GET.get("limit", 30)), 1), 200)
    except ValueError:
        limit = 30

    qs = (
        RepairRequest.objects
        .select_related(*REQUEST_SELECT_RELATED)
        .filter(status__name__in=RequestStatus.ACTIVE)
        .order_by("-created_at")[:limit]
    )
    result = [serialize(r) async for r in qs]  # асинхронная итерация по queryset
    return JsonResponse(result, safe=False, json_dumps_params=JSON_PARAMS)


@csrf_exempt
@require_POST
async def create_repair_request(request):
    """
    POST /api/requests/create/
    Тело (JSON): equipment, created_by, description, priority (1..3, необяз.), engineer (необяз.)
    Создание заявки. Асинхронное ДОБАВЛЕНИЕ.
    """
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _error({"detail": "Некорректный JSON."})

    if not isinstance(data, dict):
        return _error({"detail": "Ожидается JSON-объект."})

    errors = {}
    equipment_id = _to_id(data.get("equipment"))
    created_by_id = _to_id(data.get("created_by"))
    engineer_id = _to_id(data.get("engineer"))

    # --- проверка входных данных (асинхронные запросы к справочникам) ---
    if not equipment_id:
        errors["equipment"] = "Выберите оборудование."
    elif not await Equipment.objects.filter(pk=equipment_id).aexists():
        errors["equipment"] = "Оборудование не найдено."

    if not created_by_id:
        errors["created_by"] = "Укажите, кто принял заявку."
    elif not await Employee.objects.filter(pk=created_by_id, is_active=True).aexists():
        errors["created_by"] = "Сотрудник не найден или не работает."

    if data.get("engineer") and not engineer_id:
        errors["engineer"] = "Инженер не найден или не работает."
    elif engineer_id and not await Employee.objects.filter(pk=engineer_id, is_active=True).aexists():
        errors["engineer"] = "Инженер не найден или не работает."

    description = str(data.get("description") or "").strip()
    if not description:
        errors["description"] = "Опишите неисправность."

    try:
        priority = int(data.get("priority") or RepairRequest.Priority.NORMAL)
        if priority not in (1, 2, 3):
            raise ValueError
    except (TypeError, ValueError):
        errors["priority"] = "Приоритет должен быть 1, 2 или 3."
        priority = None

    if errors:
        return _error(errors)

    # --- создание ---
    number = await agenerate_request_number()  # REQ-2026-000123, атомарно через sequence
    status = await RequestStatus.objects.aget(name=RequestStatus.ACCEPTED)
    req = await RepairRequest.objects.acreate(  # асинхронный INSERT
        request_number=number,
        equipment_id=equipment_id,
        status=status,
        created_by_id=created_by_id,
        engineer_id=engineer_id,
        description=description,
        priority=priority,
    )

    # Перечитываем вместе со справочниками, чтобы вернуть названия, а не id.
    req = await RepairRequest.objects.select_related(*REQUEST_SELECT_RELATED).aget(pk=req.pk)
    return JsonResponse(serialize(req), status=201, json_dumps_params=JSON_PARAMS)


def _to_id(value) -> int | None:
    """id из JSON: положительное целое или None (для пустых и некорректных значений)."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _error(errors: dict, status: int = 400):
    return JsonResponse(errors, status=status, json_dumps_params=JSON_PARAMS)
