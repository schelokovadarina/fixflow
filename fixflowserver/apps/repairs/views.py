"""
Синхронные REST-эндпоинты для заявок, работ и запчастей по заявке (DRF ViewSet'ы).

Асинхронные вью (список активных заявок, создание заявки) — в async_views.py.
"""

from django.db.models import Prefetch, Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.response import Response

from apps.catalog.models import RequestStatus

from .models import RepairRequest, RequestPart, RequestWork
from .serializers import (
    RepairRequestDetailSerializer,
    RepairRequestListSerializer,
    RepairRequestUpdateSerializer,
    RequestPartSerializer,
    RequestWorkSerializer,
)

# Всё, что нужно сериализатору заявки, — одним SQL-запросом с JOIN (без N+1).
REQUEST_SELECT_RELATED = [
    "equipment__equipment_type",
    "equipment__manufacturer",
    "status",
    "engineer",
    "created_by",
]


def request_queryset():
    return RepairRequest.objects.select_related(*REQUEST_SELECT_RELATED)


@extend_schema_view(
    list=extend_schema(
        summary="Список заявок с фильтрами",
        parameters=[
            OpenApiParameter("status", int, description="id статуса"),
            OpenApiParameter("engineer", int, description="id инженера"),
            OpenApiParameter("priority", int, description="Приоритет 1..3"),
            OpenApiParameter("active", bool, description="Только незакрытые заявки"),
            OpenApiParameter("search", str, description="Поиск по номеру, описанию, оборудованию"),
        ],
    ),
    retrieve=extend_schema(summary="Карточка заявки с работами, запчастями и стоимостью"),
    partial_update=extend_schema(
        summary="Изменить оборудование, описание или приоритет",
        request=RepairRequestUpdateSerializer,
        responses=RepairRequestDetailSerializer,
    ),
)
class RepairRequestViewSet(viewsets.ModelViewSet):
    """
    Заявки на ремонт.

    Создание — асинхронной вью POST /api/requests/create/ (async ORM).
    Смена статуса, назначение инженера, закрытие — отдельными действиями
    с транзакциями и блокировками (этап 4).
    """

    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = request_queryset()
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                Prefetch("works", queryset=RequestWork.objects.select_related("work_type")),
                Prefetch("parts", queryset=RequestPart.objects.select_related("part")),
            )
            return qs

        params = self.request.query_params
        if status_id := params.get("status"):
            qs = qs.filter(status_id=status_id)
        if engineer_id := params.get("engineer"):
            qs = qs.filter(engineer_id=engineer_id)
        if priority := params.get("priority"):
            qs = qs.filter(priority=priority)
        if params.get("active") in ("1", "true"):
            qs = qs.filter(status__name__in=RequestStatus.ACTIVE)
        if search := params.get("search"):
            qs = qs.filter(
                Q(request_number__icontains=search)
                | Q(description__icontains=search)
                | Q(equipment__equipment_name__icontains=search)
                | Q(equipment__inventory_number__icontains=search)
            )
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return RepairRequestListSerializer
        if self.action in ("update", "partial_update"):
            return RepairRequestUpdateSerializer
        return RepairRequestDetailSerializer

    def perform_update(self, serializer):
        # Любое изменение заявки увеличивает version (оптимистичная блокировка;
        # проверка ожидаемой версии и блокировка строки добавляются на этапе 4).
        instance = serializer.instance
        serializer.save(version=instance.version + 1, updated_at=timezone.now())

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        # В ответ отдаём полную карточку с названиями, а не только изменённые поля.
        instance = self.get_queryset().get(pk=kwargs["pk"])
        return Response(RepairRequestDetailSerializer(instance).data)


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("request", int, description="id заявки"),
]))
class RequestWorkViewSet(viewsets.ModelViewSet):
    """Работы по заявке. Цена подставляется из справочника видов работ на момент добавления."""

    serializer_class = RequestWorkSerializer

    def get_queryset(self):
        qs = RequestWork.objects.select_related("work_type")
        if request_id := self.request.query_params.get("request"):
            qs = qs.filter(request_id=request_id)
        return qs


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("request", int, description="id заявки"),
]))
class RequestPartViewSet(viewsets.ModelViewSet):
    """
    Запчасти по заявке. Цена подставляется из справочника на момент добавления.
    Списание со склада — при закрытии заявки, в одной транзакции (этап 4).
    """

    serializer_class = RequestPartSerializer

    def get_queryset(self):
        qs = RequestPart.objects.select_related("part")
        if request_id := self.request.query_params.get("request"):
            qs = qs.filter(request_id=request_id)
        return qs
