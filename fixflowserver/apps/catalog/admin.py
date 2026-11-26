from django.contrib import admin

from .models import Equipment, EquipmentType, Manufacturer, Part, RequestStatus, WorkType


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["equipment_name", "inventory_number", "serial_number", "equipment_type", "manufacturer"]
    list_filter = ["equipment_type", "manufacturer"]
    search_fields = ["equipment_name", "inventory_number", "serial_number"]
    list_select_related = ["equipment_type", "manufacturer"]


@admin.register(RequestStatus)
class RequestStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "base_price"]
    search_fields = ["name"]


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ["name", "article", "price", "stock_qty"]
    search_fields = ["name", "article"]
