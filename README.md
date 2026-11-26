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
python manage.py runserver
```

Проверка: http://127.0.0.1:8000/api/health/ — должно вернуть `"status": "ok"` и `"isolation_level": "read committed"`.

### 3. Клиент (fixflowclient)

_Будет добавлено на этапе 3._

## Развёртывание

_Будет добавлено на этапе 5. URL развёрнутого приложения: —_
