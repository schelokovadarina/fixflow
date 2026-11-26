from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets

from .models import Equipment, EquipmentType, Manufacturer, Part, RequestStatus, WorkType
from .serializers import (
    EquipmentSerializer,
    EquipmentTypeSerializer,
    ManufacturerSerializer,
    PartSerializer,
    RequestStatusSerializer,
    WorkTypeSerializer,
)

SEARCH_PARAM = OpenApiParameter("search", str, description="Поиск по названию")


class EquipmentTypeViewSet(viewsets.ModelViewSet):
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer


class ManufacturerViewSet(viewsets.ModelViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("search", str, description="Поиск по наименованию, инвентарному или серийному номеру"),
]))
class EquipmentViewSet(viewsets.ModelViewSet):
    serializer_class = EquipmentSerializer

    def get_queryset(self):
        qs = Equipment.objects.select_related("equipment_type", "manufacturer")
        if search := self.request.query_params.get("search"):
            qs = qs.filter(
                Q(equipment_name__icontains=search)
                | Q(inventory_number__icontains=search)
                | Q(serial_number__icontains=search)
            )
        return qs


class RequestStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """Статусы — фиксированный справочник: используются в бизнес-логике, поэтому только чтение."""

    queryset = RequestStatus.objects.all()
    serializer_class = RequestStatusSerializer


class WorkTypeViewSet(viewsets.ModelViewSet):
    queryset = WorkType.objects.all()
    serializer_class = WorkTypeSerializer


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("search", str, description="Поиск по названию или артикулу"),
]))
class PartViewSet(viewsets.ModelViewSet):
    serializer_class = PartSerializer

    def get_queryset(self):
        qs = Part.objects.all()
        if search := self.request.query_params.get("search"):
            qs = qs.filter(Q(name__icontains=search) | Q(article__icontains=search))
        return qs
