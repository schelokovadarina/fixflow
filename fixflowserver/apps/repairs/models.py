"""Заявки на ремонт, работы и запчасти по заявке."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Now

from apps.catalog.models import Equipment, Part, RequestStatus, WorkType
from apps.staff.models import Employee


def default_status_id():
    """Статус по умолчанию для новой заявки — «Принята»."""
    return RequestStatus.objects.only("id").get(name=RequestStatus.ACCEPTED).pk


class RepairRequest(models.Model):
    """
    Заявка на ремонт (таблица repair_requests) — главная оперативная таблица.

    Структура зафиксирована в отчёте №2. Поле version используется
    для оптимистичной блокировки: увеличивается при каждом изменении заявки.
    """

    class Priority(models.IntegerChoices):
        HIGH = 1, "Высокий"
        NORMAL = 2, "Обычный"
        LOW = 3, "Низкий"

    id = models.BigAutoField(primary_key=True)
    request_number = models.CharField("Номер заявки", max_length=25, unique=True)
    equipment = models.ForeignKey(
        Equipment, on_delete=models.PROTECT, related_name="repair_requests", verbose_name="Оборудование"
    )
    status = models.ForeignKey(
        RequestStatus,
        on_delete=models.PROTECT,
        default=default_status_id,
        related_name="repair_requests",
        verbose_name="Статус",
    )
    created_by = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="created_requests", verbose_name="Кто создал"
    )
    engineer = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_requests",
        verbose_name="Инженер",
    )
    description = models.TextField("Описание неисправности")
    priority = models.SmallIntegerField(
        "Приоритет",
        choices=Priority.choices,
        default=Priority.NORMAL,
        db_default=Priority.NORMAL,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
    )
    created_at = models.DateTimeField("Создана", db_default=Now())
    updated_at = models.DateTimeField("Изменена", db_default=Now())
    completed_at = models.DateTimeField("Завершена", null=True, blank=True)
    version = models.IntegerField("Версия", default=1, db_default=1)

    class Meta:
        db_table = "repair_requests"
        verbose_name = "Заявка на ремонт"
        verbose_name_plural = "Заявки на ремонт"
        ordering = ["-created_at"]
        # Индексы по status_id, engineer_id и т.п. Django создаёт автоматически для FK;
        # здесь добавлен только индекс для сортировки списка «сначала новые».
        indexes = [
            models.Index(fields=["-created_at"], name="repair_req_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(description__regex=r"^\s*$"),
                name="repair_requests_description_not_empty",
            ),
            models.CheckConstraint(
                condition=Q(priority__gte=1, priority__lte=3),
                name="repair_requests_priority_1_3",
            ),
            models.CheckConstraint(condition=Q(version__gte=1), name="repair_requests_version_gte_1"),
            models.CheckConstraint(
                condition=Q(completed_at__isnull=True) | Q(completed_at__gte=F("created_at")),
                name="repair_requests_completed_after_created",
            ),
        ]

    def __str__(self):
        return self.request_number


class RequestWork(models.Model):
    """Работа по заявке (таблица request_works). price — цена на момент добавления."""

    request = models.ForeignKey(
        RepairRequest, on_delete=models.CASCADE, related_name="works", verbose_name="Заявка"
    )
    work_type = models.ForeignKey(
        WorkType, on_delete=models.PROTECT, related_name="request_works", verbose_name="Вид работ"
    )
    qty = models.IntegerField("Количество", default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField("Цена, ₽", max_digits=10, decimal_places=2)

    class Meta:
        db_table = "request_works"
        verbose_name = "Работа по заявке"
        verbose_name_plural = "Работы по заявке"
        constraints = [
            models.CheckConstraint(condition=Q(qty__gt=0), name="request_works_qty_gt_0"),
            models.CheckConstraint(condition=Q(price__gte=0), name="request_works_price_gte_0"),
        ]

    def __str__(self):
        return f"{self.work_type} × {self.qty}"


class RequestPart(models.Model):
    """Запчасть по заявке (таблица request_parts). price — цена на момент списания."""

    request = models.ForeignKey(
        RepairRequest, on_delete=models.CASCADE, related_name="parts", verbose_name="Заявка"
    )
    part = models.ForeignKey(
        Part, on_delete=models.PROTECT, related_name="request_parts", verbose_name="Запчасть"
    )
    qty = models.IntegerField("Количество", default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField("Цена, ₽", max_digits=10, decimal_places=2)

    class Meta:
        db_table = "request_parts"
        verbose_name = "Запчасть по заявке"
        verbose_name_plural = "Запчасти по заявке"
        constraints = [
            models.CheckConstraint(condition=Q(qty__gt=0), name="request_parts_qty_gt_0"),
            models.CheckConstraint(condition=Q(price__gte=0), name="request_parts_price_gte_0"),
        ]

    def __str__(self):
        return f"{self.part} × {self.qty}"
