from django.contrib import admin

from .models import RepairRequest, RequestPart, RequestWork
from .numbering import generate_request_number


class RequestWorkInline(admin.TabularInline):
    model = RequestWork
    extra = 0


class RequestPartInline(admin.TabularInline):
    model = RequestPart
    extra = 0


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = [
        "request_number", "equipment", "status", "engineer", "priority", "created_at", "completed_at",
    ]
    list_filter = ["status", "priority", "engineer"]
    search_fields = ["request_number", "description", "equipment__equipment_name", "equipment__inventory_number"]
    list_select_related = ["equipment", "status", "engineer", "created_by"]
    readonly_fields = ["request_number", "created_at", "updated_at", "version"]
    inlines = [RequestWorkInline, RequestPartInline]

    def save_model(self, request, obj, form, change):
        if not obj.request_number:
            obj.request_number = generate_request_number()
        super().save_model(request, obj, form, change)
