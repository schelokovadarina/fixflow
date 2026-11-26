"""
Заполнение БД тестовыми данными.

    python manage.py seed           # справочники + заявки (если заявок ещё нет)
    python manage.py seed --reset   # удалить все заявки и создать заново

Справочники создаются через update_or_create — команду можно запускать повторно.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from apps.catalog.models import Equipment, EquipmentType, Manufacturer, Part, RequestStatus, WorkType
from apps.repairs.models import RepairRequest, RequestPart, RequestWork
from apps.repairs.numbering import SEQUENCE_NAME, generate_request_number
from apps.staff.models import Department, Employee, Position

POSITIONS = ["Приёмщик", "Инженер-ремонтник", "Ведущий инженер", "Руководитель сервисной службы"]

DEPARTMENTS = ["Служба приёма оборудования", "Сервисный отдел", "Отдел ИТ-инфраструктуры", "Руководство"]

# (ФИО, email, телефон, должность, подразделение, работает)
EMPLOYEES = [
    ("Смирнова Ольга Викторовна", "o.smirnova@fixflow.local", "+7 (900) 111-22-01", "Приёмщик", "Служба приёма оборудования", True),
    ("Кузнецов Андрей Павлович", "a.kuznetsov@fixflow.local", "+7 (900) 111-22-02", "Приёмщик", "Служба приёма оборудования", True),
    ("Иванов Сергей Николаевич", "s.ivanov@fixflow.local", "+7 (900) 111-22-03", "Ведущий инженер", "Сервисный отдел", True),
    ("Петров Дмитрий Алексеевич", "d.petrov@fixflow.local", "+7 (900) 111-22-04", "Инженер-ремонтник", "Сервисный отдел", True),
    ("Соколова Анна Игоревна", "a.sokolova@fixflow.local", "+7 (900) 111-22-05", "Инженер-ремонтник", "Сервисный отдел", True),
    ("Волков Максим Олегович", "m.volkov@fixflow.local", "+7 (900) 111-22-06", "Инженер-ремонтник", "Отдел ИТ-инфраструктуры", True),
    ("Морозова Елена Сергеевна", "e.morozova@fixflow.local", "+7 (900) 111-22-07", "Инженер-ремонтник", "Отдел ИТ-инфраструктуры", True),
    ("Новиков Павел Романович", "p.novikov@fixflow.local", "+7 (900) 111-22-08", "Инженер-ремонтник", "Сервисный отдел", False),
    ("Лебедева Ирина Михайловна", "i.lebedeva@fixflow.local", "+7 (900) 111-22-09", "Руководитель сервисной службы", "Руководство", True),
]

EQUIPMENT_TYPES = ["Ноутбук", "Системный блок", "Монитор", "Принтер", "МФУ", "ИБП", "Сетевое оборудование", "Проектор"]

MANUFACTURERS = ["HP", "Lenovo", "Dell", "Canon", "Epson", "APC", "Huawei", "Acer"]

# (наименование, инв. номер, серийный номер, тип, производитель)
EQUIPMENT = [
    ("Ноутбук ThinkPad E14", "INV-00101", "PF3K9A21", "Ноутбук", "Lenovo"),
    ("Ноутбук ThinkPad E14", "INV-00102", "PF3K9A35", "Ноутбук", "Lenovo"),
    ("Ноутбук ProBook 450 G9", "INV-00103", "5CD2341XYZ", "Ноутбук", "HP"),
    ("Ноутбук Latitude 5430", "INV-00104", "DL5430-7781", "Ноутбук", "Dell"),
    ("Системный блок OptiPlex 7010", "INV-00201", "DL7010-1120", "Системный блок", "Dell"),
    ("Системный блок ThinkCentre M70s", "INV-00202", "S1A8K22M", "Системный блок", "Lenovo"),
    ("Системный блок ProDesk 400 G7", "INV-00203", "CZC1239ABC", "Системный блок", "HP"),
    ("Монитор P2422H", "INV-00301", "CN0DP2422H", "Монитор", "Dell"),
    ("Монитор Vero V247Y", "INV-00302", "MMTMKEE003", "Монитор", "Acer"),
    ("Принтер LaserJet Pro M404dn", "INV-00401", "PHBL412345", "Принтер", "HP"),
    ("Принтер i-SENSYS LBP223dw", "INV-00402", "XKC0098812", "Принтер", "Canon"),
    ("МФУ i-SENSYS MF445dw", "INV-00501", "XKF0021134", "МФУ", "Canon"),
    ("МФУ L6290", "INV-00502", "X8K2004411", "МФУ", "Epson"),
    ("ИБП Back-UPS 950VA", "INV-00601", "3B2205X11234", "ИБП", "APC"),
    ("Коммутатор S220-24T4X", "INV-00701", "2102353AG01", "Сетевое оборудование", "Huawei"),
    ("Проектор EB-X49", "INV-00801", "X5NF2300456", "Проектор", "Epson"),
]

# (название, порядок)
STATUSES = [
    (RequestStatus.ACCEPTED, 1),
    (RequestStatus.IN_PROGRESS, 2),
    (RequestStatus.WAITING_PARTS, 3),
    (RequestStatus.DONE, 4),
    (RequestStatus.ISSUED, 5),
    (RequestStatus.REJECTED, 6),
]

WORK_TYPES = [
    ("Диагностика", "800.00"),
    ("Чистка от пыли и замена термопасты", "1500.00"),
    ("Замена матрицы", "2000.00"),
    ("Замена клавиатуры", "1200.00"),
    ("Установка и настройка ОС", "1800.00"),
    ("Замена накопителя с переносом данных", "1600.00"),
    ("Ремонт узла подачи бумаги", "2200.00"),
    ("Замена аккумуляторной батареи ИБП", "700.00"),
    ("Ремонт блока питания", "2500.00"),
]

# (название, артикул, цена, остаток)
PARTS = [
    ("SSD-накопитель 512 ГБ", "SSD-512-NV", "4200.00", 12),
    ("Оперативная память DDR4 8 ГБ", "RAM-DDR4-8", "2300.00", 15),
    ("Термопаста Arctic MX-4, 4 г", "TP-MX4-4G", "650.00", 30),
    ("Матрица 14\" FHD IPS", "LCD-14-FHD", "6800.00", 3),
    ("Клавиатура ThinkPad E14", "KB-TP-E14", "2900.00", 4),
    ("Ролик захвата бумаги HP M404", "RL-HP-M404", "1100.00", 6),
    ("Ролик захвата бумаги Canon MF445", "RL-CN-MF445", "1250.00", 2),
    ("Аккумуляторная батарея 12 В 9 Ач", "BAT-12V-9AH", "2100.00", 8),
    ("Блок питания ATX 500 Вт", "PSU-ATX-500", "3900.00", 5),
    ("Кабель питания монитора", "CBL-PWR-C13", "250.00", 25),
]

FAULTS = [
    "Не включается, индикатор питания не горит.",
    "Сильно греется и выключается через 10–15 минут работы.",
    "На экране вертикальные полосы, изображение мерцает.",
    "Не работают несколько клавиш на клавиатуре.",
    "Медленно работает, долго загружается система.",
    "Не захватывает бумагу из лотка, замятие при печати.",
    "Печатает бледно, полосы на отпечатках.",
    "Сканер не определяется по сети.",
    "ИБП пищит и не держит нагрузку при отключении сети.",
    "Не видит жёсткий диск при загрузке.",
    "Периодически пропадает сеть на портах 1–8.",
    "Не включается лампа проектора, мигает индикатор.",
    "Треснул корпус, не фиксируется крышка.",
    "Нет изображения на мониторе, подсветка работает.",
]

# Сколько заявок в каком статусе создать (итого 18).
STATUS_PLAN = [
    (RequestStatus.ACCEPTED, 4),
    (RequestStatus.IN_PROGRESS, 4),
    (RequestStatus.WAITING_PARTS, 3),
    (RequestStatus.DONE, 3),
    (RequestStatus.ISSUED, 3),
    (RequestStatus.REJECTED, 1),
]


class Command(BaseCommand):
    help = "Заполняет справочники и создаёт тестовые заявки на ремонт."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Удалить все заявки и создать заново.")

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        rnd = random.Random(2026)  # фиксированное зерно — одинаковые данные при каждом запуске

        self._seed_references()

        if reset:
            deleted, _ = RepairRequest.objects.all().delete()
            with connection.cursor() as cur:
                cur.execute(f"ALTER SEQUENCE {SEQUENCE_NAME} RESTART WITH 1")
            self._restore_stock()
            self.stdout.write(f"Удалено записей заявок (с работами и запчастями): {deleted}")
        elif RepairRequest.objects.exists():
            self.stdout.write(self.style.WARNING(
                "Заявки уже есть — пропускаю. Для пересоздания: python manage.py seed --reset"
            ))
            return

        count = self._seed_requests(rnd)
        self.stdout.write(self.style.SUCCESS(f"Готово: справочники заполнены, создано заявок: {count}"))

    # --- справочники ---------------------------------------------------------

    def _seed_references(self):
        positions = {n: Position.objects.get_or_create(name=n)[0] for n in POSITIONS}
        departments = {n: Department.objects.get_or_create(name=n)[0] for n in DEPARTMENTS}
        for full_name, email, phone, pos, dep, active in EMPLOYEES:
            Employee.objects.update_or_create(
                email=email,
                defaults=dict(
                    full_name=full_name, phone=phone, position=positions[pos],
                    department=departments[dep], is_active=active,
                ),
            )

        types = {n: EquipmentType.objects.get_or_create(name=n)[0] for n in EQUIPMENT_TYPES}
        manufacturers = {n: Manufacturer.objects.get_or_create(name=n)[0] for n in MANUFACTURERS}
        for name, inv, serial, type_name, manuf in EQUIPMENT:
            Equipment.objects.update_or_create(
                inventory_number=inv,
                defaults=dict(
                    equipment_name=name, serial_number=serial,
                    equipment_type=types[type_name], manufacturer=manufacturers[manuf],
                ),
            )

        for name, order in STATUSES:
            RequestStatus.objects.update_or_create(name=name, defaults={"order": order})
        for name, price in WORK_TYPES:
            WorkType.objects.update_or_create(name=name, defaults={"base_price": Decimal(price)})
        # Остаток задаётся только при создании запчасти: при повторном запуске
        # не затираем остатки, уже уменьшенные списаниями по заявкам.
        for name, article, price, qty in PARTS:
            Part.objects.update_or_create(
                article=article,
                defaults=dict(name=name, price=Decimal(price)),
                create_defaults=dict(name=name, price=Decimal(price), stock_qty=qty),
            )

    def _restore_stock(self):
        """Начальные остатки склада — при пересоздании заявок."""
        for _, article, _, qty in PARTS:
            Part.objects.filter(article=article).update(stock_qty=qty)

    # --- заявки --------------------------------------------------------------

    def _seed_requests(self, rnd):
        now = timezone.now()
        statuses = {s.name: s for s in RequestStatus.objects.all()}
        receivers = list(Employee.objects.filter(position__name="Приёмщик"))
        engineers = list(Employee.objects.filter(
            position__name__in=["Инженер-ремонтник", "Ведущий инженер"], is_active=True
        ))
        equipment = list(Equipment.objects.all())
        work_types = list(WorkType.objects.all())
        parts = list(Part.objects.all())

        # Сначала план заявок, отсортированный по дате — чтобы номера шли по порядку создания.
        plan = []
        for status_name, n in STATUS_PLAN:
            for _ in range(n):
                # закрытые заявки — постарше, новые — свежие
                max_age = 45 if status_name in (RequestStatus.DONE, RequestStatus.ISSUED) else 20
                age = timedelta(days=rnd.randint(1, max_age), hours=rnd.randint(0, 8), minutes=rnd.randint(0, 59))
                plan.append((now - age, status_name))
        plan.sort(key=lambda p: p[0])

        for created_at, status_name in plan:
            status = statuses[status_name]
            # version = 1 + число изменений заявки (назначение инженера, смены статуса)
            steps = {
                RequestStatus.ACCEPTED: 0, RequestStatus.REJECTED: 1, RequestStatus.IN_PROGRESS: 2,
                RequestStatus.WAITING_PARTS: 3, RequestStatus.DONE: 3, RequestStatus.ISSUED: 4,
            }[status_name]
            has_engineer = status_name not in (RequestStatus.ACCEPTED, RequestStatus.REJECTED)
            completed_at = None
            if status_name in (RequestStatus.DONE, RequestStatus.ISSUED):
                completed_at = min(created_at + timedelta(days=rnd.randint(1, 5), hours=rnd.randint(1, 6)), now)
            updated_at = completed_at or created_at + timedelta(hours=rnd.randint(0, 20)) * min(steps, 1)

            req = RepairRequest.objects.create(
                request_number=generate_request_number(),
                equipment=rnd.choice(equipment),
                status=status,
                created_by=rnd.choice(receivers),
                engineer=rnd.choice(engineers) if has_engineer else None,
                description=rnd.choice(FAULTS),
                priority=rnd.choices([1, 2, 3], weights=[2, 5, 2])[0],
                created_at=created_at,
                updated_at=min(updated_at, now),
                completed_at=completed_at,
                version=1 + steps,
            )

            # Работы: у заявок в работе/ожидании/закрытых. Цена — из справочника на момент добавления.
            if status_name in (RequestStatus.IN_PROGRESS, RequestStatus.WAITING_PARTS,
                               RequestStatus.DONE, RequestStatus.ISSUED):
                for wt in rnd.sample(work_types, k=rnd.randint(1, 3)):
                    RequestWork.objects.create(request=req, work_type=wt, qty=1, price=wt.base_price)

            # Запчасти: у закрытых заявок — списаны со склада.
            if status_name in (RequestStatus.DONE, RequestStatus.ISSUED):
                for part in rnd.sample(parts, k=rnd.randint(1, 2)):
                    part.refresh_from_db()
                    if part.stock_qty >= 1:
                        RequestPart.objects.create(request=req, part=part, qty=1, price=part.price)
                        part.stock_qty -= 1
                        part.save(update_fields=["stock_qty"])

        return len(plan)
