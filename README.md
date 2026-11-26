# FixFlow

Информационная система учёта ремонта оборудования предприятия: заявки на ремонт, назначение инженеров, учёт работ и запчастей, контроль сроков.

- **приёмщик** оформляет заявку на поступившее оборудование;
- **инженер** ведёт ремонт, фиксирует работы и запчасти;
- **руководитель** отслеживает статусы, сроки и загрузку сотрудников.

## Стек

| Часть | Технологии |
|---|---|
| Backend | Python 3.12, Django 5.2, Django REST Framework, drf-spectacular, psycopg 3 |
| Frontend | React 18, TypeScript, Vite, react-router-dom, axios |
| БД | PostgreSQL 16 (уровень изоляции Read Committed) |
| Прод | gunicorn + uvicorn worker (ASGI), whitenoise |

## Структура

```
fixflowserver/   сервер: Django-проект (config/) и приложения apps/staff, apps/catalog, apps/repairs
fixflowclient/   клиент: React + TypeScript (Vite)
docs/            диаграммы и материалы пояснительной записки
```

## Запуск с нуля (Windows / PowerShell)

### 1. База данных

Установите PostgreSQL 16 и создайте базу:

```powershell
psql -U postgres -h localhost -c "CREATE DATABASE fixflow ENCODING 'UTF8';"
```

### 2. Сервер (fixflowserver)

```powershell
cd fixflowserver
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # затем отредактируйте .env (SECRET_KEY, пароль БД)
python manage.py migrate
python manage.py seed               # справочники + 18 тестовых заявок
python manage.py createsuperuser    # учётная запись для админки
python manage.py runserver
```

- http://127.0.0.1:8000/api/health/ — проверка: `"status": "ok"`, `"isolation_level": "read committed"`;
- http://127.0.0.1:8000/admin/ — админка Django.

`python manage.py seed --reset` — удалить все заявки, вернуть начальные остатки склада и создать заявки заново.

## База данных

12 таблиц: справочники `positions`, `departments`, `equipment_types`, `manufacturers`, `request_statuses`, `work_types`, `parts`; основные `employees`, `equipment`, `repair_requests`; связи M:N `request_works`, `request_parts`.

Ограничения целостности заданы на уровне БД (CHECK): `priority` 1..3, `version >= 1`, непустое `description`, `completed_at >= created_at`, `qty > 0`, `stock_qty >= 0`, цены `>= 0`.

Номер заявки `REQ-<год>-<6 цифр>` берётся из последовательности PostgreSQL `repair_request_number_seq` — `nextval()` атомарна, поэтому параллельное создание заявок не даёт дублей.

### 3. Клиент (fixflowclient)

_Будет добавлено на этапе 3._

## Развёртывание

_Будет добавлено на этапе 5. URL развёрнутого приложения: —_
