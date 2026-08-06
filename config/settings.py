import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv() # Загружает переменные из .env в os.environ

# Базовая директория
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ (в продакшене лучше вынести в .env)
SECRET_KEY = 'django-insecure-key-here'

# Режим отладки (в Docker лучше ставить True для разработки)
DEBUG = True

# ВАЖНО: Разрешаем работу внутри Docker
ALLOWED_HOSTS = ['*']

# Приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Твои кастомные приложения
    'sports_data',
    'execution_module',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls' # Убедись, что путь соответствует твоей структуре

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# База данных (у тебя PostgreSQL в Docker)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': '5432',
    }
}

# Язык и таймзона
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Настройки для разработки и статики ---
# Путь, где будут собираться статические файлы (CSS, JS админки и т.д.)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Медиа-файлы (если позже захочешь хранить аватары команд или графики)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- Безопасность и окружение ---
# Чтобы Django понимал, что он за прокси-сервером (важно для Docker)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')