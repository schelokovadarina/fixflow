from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import RepairRequest, RequestPart, RequestWork


def money(value: Decimal) -> str:
    """Денежная сумма строкой с двумя знаками — в том же формате, что цены (DecimalField)."""
    return f"{value:.2f}"


# --- Работы и запчасти по заявке ------------------------------------------------

class RequestWorkSerializer(serializers.ModelSerializer):
    work_type_name = serializers.CharField(source="work_type.name", read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = RequestWork
        fields = ["id", "request", "work_type", "work_type_name", "qty", "price", "total"]
        # Цена не вводится вручную — фиксируется из справочника на момент добавления.
        read_only_fields = ["price"]
        extra_kwargs = {"qty": {"min_value": 1}}

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_total(self, obj) -> str:
        return money(obj.price * obj.qty)

    def create(self, validated_data):
        validated_data["price"] = validated_data["work_type"].base_price
        return super().create(validated_data)


class RequestPartSerializer(serializers.ModelSerializer):
    part_name = serializers.CharField(source="part.name", read_only=True)
    part_article = serializers.CharField(source="part.article", read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = RequestPart
        fields = ["id", "request", "part", "part_name", "part_article", "qty", "price", "total"]
        # Цена фиксируется из справочника запчастей на момент добавления.
        read_only_fields = ["price"]
        extra_kwargs = {"qty": {"min_value": 1}}

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_total(self, obj) -> str:
        return money(obj.price * obj.qty)

    def create(self, validated_data):
        validated_data["price"] = validated_data["part"].price
        return super().create(validated_data)


# --- Заявка на ремонт -----------------------------------------------------------

class RepairRequestListSerializer(serializers.ModelSerializer):
    """
    Заявка для списков. Все связанные данные — читаемыми названиями
    (equipment_name, status_name, engineer_name, ...).

    Сериализатор не делает запросов к БД, если queryset построен с
    select_related (см. RepairRequestViewSet.get_queryset) — поэтому его можно
    безопасно использовать и в асинхронных вью.
    """

    equipment_name = serializers.CharField(source="equipment.equipment_name", read_only=True)
    inventory_number = serializers.CharField(source="equipment.inventory_number", read_only=True)
    type_name = serializers.CharField(source="equipment.equipment_type.name", read_only=True)
    manufacturer_name = serializers.CharField(source="equipment.manufacturer.name", read_only=True)
    status_name = serializers.CharField(source="status.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    engineer_name = serializers.SerializerMethodField()
    priority_name = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = RepairRequest
        fields = [
            "id", "request_number",
            "equipment", "equipment_name", "inventory_number", "type_name", "manufacturer_name",
            "status", "status_name",
            "engineer", "engineer_name",
            "created_by", "created_by_name",
            "priority", "priority_name",
            "description",
            "created_at", "updated_at", "completed_at",
            "version",
        ]
        read_only_fields = fields

    def get_engineer_name(self, obj) -> str | None:
        return obj.engineer.full_name if obj.engineer else None


class RepairRequestDetailSerializer(RepairRequestListSerializer):
    """Карточка заявки: плюс работы, запчасти и стоимость ремонта."""

    works = RequestWorkSerializer(many=True, read_only=True)
    parts = RequestPartSerializer(many=True, read_only=True)
    works_total = serializers.SerializerMethodField()
    parts_total = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()

    class Meta(RepairRequestListSerializer.Meta):
        fields = RepairRequestListSerializer.Meta.fields + [
            "works", "parts", "works_total", "parts_total", "total_cost",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_works_total(self, obj) -> str:
        return money(sum((w.price * w.qty for w in obj.works.all()), Decimal("0")))

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_parts_total(self, obj) -> str:
        return money(sum((p.price * p.qty for p in obj.parts.all()), Decimal("0")))

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_total_cost(self, obj) -> str:
        return money(Decimal(self.get_works_total(obj)) + Decimal(self.get_parts_total(obj)))


class RepairRequestUpdateSerializer(serializers.ModelSerializer):
    """
    Редактирование описательных полей заявки: оборудование, описание, приоритет.
    Статус и инженер меняются отдельными действиями с блокировками (этап 4).
    """

    class Meta:
        model = RepairRequest
        fields = ["equipment", "description", "priority"]

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("Описание неисправности не может быть пустым.")
        return value.strip()
