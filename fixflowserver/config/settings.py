"""
Настройки проекта FixFlow.

Все чувствительные параметры (секретный ключ, доступ к БД) читаются из файла .env
(см. .env.example). Сам .env в репозиторий не попадает.
"""

from pathlib import Path

import environ
from psycopg import IsolationLevel

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    DB_HOST=(str, "localhost"),
    DB_PORT=(int, 5432),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")


# --- Приложения -------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # сторонние
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    # приложения проекта
    "apps.staff",
    "apps.catalog",
    "apps.repairs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --- База данных ------------------------------------------------------------
# PostgreSQL 16, драйвер psycopg 3.
#
# УРОВЕНЬ ИЗОЛЯЦИИ: READ COMMITTED.
# Это уровень по умолчанию в PostgreSQL; здесь он задан ЯВНО, чтобы было видно,
# где он настраивается. Обоснование: все операции кратковременные и затрагивают
# отдельные строки (заявка по PK, строка склада), а гонки закрываются
# блокировками строк (SELECT ... FOR UPDATE) и проверкой поля version.
# Serializable не требуется.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "OPTIONS": {
            "isolation_level": IsolationLevel.READ_COMMITTED,
        },
    }
}


# --- Пароли -----------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Локализация ------------------------------------------------------------

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True


# --- Статика ----------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- REST API ---------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FixFlow API",
    "DESCRIPTION": "Учёт ремонта оборудования предприятия",
    "VERSION": "1.0.0",
}

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
