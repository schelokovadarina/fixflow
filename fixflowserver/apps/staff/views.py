from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets

from .models import Department, Employee, Position
from .serializers import DepartmentSerializer, EmployeeSerializer, PositionSerializer

# Должности, сотрудники с которыми могут быть назначены на заявку.
ENGINEER_POSITIONS = ["Инженер-ремонтник", "Ведущий инженер"]


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


@extend_schema_view(
    list=extend_schema(parameters=[
        OpenApiParameter("engineers", bool, description="Только инженеры (для назначения на заявку)"),
        OpenApiParameter("active", bool, description="Только работающие сотрудники"),
        OpenApiParameter("search", str, description="Поиск по ФИО, email, телефону"),
    ])
)
class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        qs = Employee.objects.select_related("position", "department")
        params = self.request.query_params
        if params.get("engineers") in ("1", "true"):
            qs = qs.filter(position__name__in=ENGINEER_POSITIONS)
        if params.get("active") in ("1", "true"):
            qs = qs.filter(is_active=True)
        if search := params.get("search"):
            qs = qs.filter(Q(full_name__icontains=search) | Q(email__icontains=search) | Q(phone__icontains=search))
        return qs
