from rest_framework import serializers

from .models import Department, Employee, Position


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["id", "name"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]


class EmployeeSerializer(serializers.ModelSerializer):
    # Читаемые названия вместо кодов справочников.
    position_name = serializers.CharField(source="position.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "full_name", "email", "phone",
            "position", "position_name",
            "department", "department_name",
            "is_active",
        ]
