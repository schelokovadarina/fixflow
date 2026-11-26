"""
Маршруты (URLconf) — «контроллер» в терминах MVC: какой URL обрабатывает какое представление.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.catalog import views as catalog
from apps.repairs import async_views
from apps.repairs import views as repairs
from apps.staff import views as staff

from . import views

router = DefaultRouter()
# сотрудники
router.register("positions", staff.PositionViewSet)
router.register("departments", staff.DepartmentViewSet)
router.register("employees", staff.EmployeeViewSet, basename="employee")
# справочники
router.register("equipment-types", catalog.EquipmentTypeViewSet)
router.register("manufacturers", catalog.ManufacturerViewSet)
router.register("equipment", catalog.EquipmentViewSet, basename="equipment")
router.register("statuses", catalog.RequestStatusViewSet)
router.register("work-types", catalog.WorkTypeViewSet)
router.register("parts", catalog.PartViewSet, basename="part")
# заявки
router.register("requests", repairs.RepairRequestViewSet, basename="repairrequest")
router.register("request-works", repairs.RequestWorkViewSet, basename="requestwork")
router.register("request-parts", repairs.RequestPartViewSet, basename="requestpart")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", views.health, name="health"),
    # Асинхронные вью — объявлены ДО router, чтобы /api/requests/active/
    # не был принят за /api/requests/<id>/.
    path("api/requests/active/", async_views.list_active_requests, name="requests-active"),
    path("api/requests/create/", async_views.create_repair_request, name="requests-create"),
    path("api/", include(router.urls)),
    # Документация API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]
