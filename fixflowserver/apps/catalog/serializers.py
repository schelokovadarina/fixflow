from rest_framework import serializers

from .models import Equipment, EquipmentType, Manufacturer, Part, RequestStatus, WorkType


class EquipmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentType
        fields = ["id", "name"]


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ["id", "name"]


class EquipmentSerializer(serializers.ModelSerializer):
    # Читаемые названия вместо кодов справочников.
    type_name = serializers.CharField(source="equipment_type.name", read_only=True)
    manufacturer_name = serializers.CharField(source="manufacturer.name", read_only=True)

    class Meta:
        model = Equipment
        fields = [
            "id", "equipment_name", "inventory_number", "serial_number",
            "equipment_type", "type_name",
            "manufacturer", "manufacturer_name",
        ]


class RequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestStatus
        fields = ["id", "name", "order"]


class WorkTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkType
        fields = ["id", "name", "base_price"]


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = ["id", "name", "article", "price", "stock_qty"]
        extra_kwargs = {"stock_qty": {"min_value": 0}}
