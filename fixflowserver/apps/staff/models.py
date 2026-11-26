"""Сотрудники, должности, подразделения."""

from django.db import models


class Position(models.Model):
    """Справочник должностей (таблица positions)."""

    name = models.CharField("Название", max_length=100, unique=True)

    class Meta:
        db_table = "positions"
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    """Справочник подразделений (таблица departments)."""

    name = models.CharField("Название", max_length=150, unique=True)

    class Meta:
        db_table = "departments"
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Employee(models.Model):
    """Сотрудник предприятия (таблица employees): приёмщик, инженер, руководитель."""

    full_name = models.CharField("ФИО", max_length=150)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    position = models.ForeignKey(
        Position, on_delete=models.PROTECT, related_name="employees", verbose_name="Должность"
    )
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="employees", verbose_name="Подразделение"
    )
    is_active = models.BooleanField("Работает", default=True)

    class Meta:
        db_table = "employees"
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name
