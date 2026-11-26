from django.contrib import admin

from .models import Department, Employee, Position


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "position", "department", "email", "phone", "is_active"]
    list_filter = ["position", "department", "is_active"]
    search_fields = ["full_name", "email", "phone"]
    list_select_related = ["position", "department"]
