"""Справочники: типы оборудования, производители, оборудование, статусы, виды работ, запчасти."""

from django.db import models
from django.db.models import Q


class EquipmentType(models.Model):
    """Тип оборудования (таблица equipment_types)."""

    name = models.CharField("Название", max_length=100, unique=True)

    class Meta:
        db_table = "equipment_types"
        verbose_name = "Тип оборудования"
        verbose_name_plural = "Типы оборудования"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Производитель (таблица manufacturers)."""

    name = models.CharField("Название", max_length=100, unique=True)

    class Meta:
        db_table = "manufacturers"
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """Единица оборудования (таблица equipment)."""

    equipment_name = models.CharField("Наименование", max_length=200)
    inventory_number = models.CharField("Инвентарный номер", max_length=50, unique=True)
    serial_number = models.CharField("Серийный номер", max_length=100, blank=True)
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.PROTECT,
        db_column="type_id",
        related_name="equipment",
        verbose_name="Тип",
    )
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, related_name="equipment", verbose_name="Производитель"
    )

    class Meta:
        db_table = "equipment"
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        ordering = ["equipment_name"]

    def __str__(self):
        return f"{self.equipment_name} ({self.inventory_number})"


class RequestStatus(models.Model):
    """Статус заявки на ремонт (таблица request_statuses)."""

    # Названия статусов используются в бизнес-логике — держим их в одном месте.
    ACCEPTED = "Принята"
    IN_PROGRESS = "В работе"
    WAITING_PARTS = "Ожидает запчасти"
    DONE = "Готова"
    ISSUED = "Выдана"
    REJECTED = "Отклонена"

    ALL = [ACCEPTED, IN_PROGRESS, WAITING_PARTS, DONE, ISSUED, REJECTED]
    ACTIVE = [ACCEPTED, IN_PROGRESS, WAITING_PARTS]  # заявка ещё не закрыта

    name = models.CharField("Название", max_length=50, unique=True)
    order = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        db_table = "request_statuses"
        verbose_name = "Статус заявки"
        verbose_name_plural = "Статусы заявок"
        ordering = ["order"]

    def __str__(self):
        return self.name


class WorkType(models.Model):
    """Вид работ с базовой ценой (таблица work_types)."""

    name = models.CharField("Название", max_length=150, unique=True)
    base_price = models.DecimalField("Базовая цена, ₽", max_digits=10, decimal_places=2)

    class Meta:
        db_table = "work_types"
        verbose_name = "Вид работ"
        verbose_name_plural = "Виды работ"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=Q(base_price__gte=0), name="work_types_base_price_gte_0"),
        ]

    def __str__(self):
        return self.name


class Part(models.Model):
    """Запчасть / ЗИП с остатком на складе (таблица parts)."""

    name = models.CharField("Название", max_length=200)
    article = models.CharField("Артикул", max_length=50, unique=True)
    price = models.DecimalField("Цена, ₽", max_digits=10, decimal_places=2)
    stock_qty = models.IntegerField("Остаток на складе", default=0)

    class Meta:
        db_table = "parts"
        verbose_name = "Запчасть"
        verbose_name_plural = "Запчасти"
        ordering = ["name"]
        constraints = [
            # Склад не может уйти в минус — проверка на уровне БД.
            models.CheckConstraint(condition=Q(stock_qty__gte=0), name="parts_stock_qty_gte_0"),
            models.CheckConstraint(condition=Q(price__gte=0), name="parts_price_gte_0"),
        ]

    def __str__(self):
        return f"{self.name} ({self.article})"
