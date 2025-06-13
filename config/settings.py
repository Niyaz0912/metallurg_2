import os
from dotenv import load_dotenv
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-for-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = ['192.168.1.180', 'localhost', '127.0.0.1']

# Debug toolbar config (disabled by default)
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: False,  # Полностью отключает toolbar
}

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap4',
    'django_tables2',
    # 'debug_toolbar',  # Раскомментируйте при необходимости

    # Custom apps
    'users',
    'production_plan',
    'shift_assignment',
    'techcard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'config.middleware.AuthRedirectMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  # Раскомментируйте при необходимости
]

# Crispy Forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

INTERNAL_IPS = ['127.0.0.1']

# Redirect URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'production_plan:list'  # Исправлено с 'production:list' на 'production_plan:list'
LOGOUT_REDIRECT_URL = 'login'

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Папка для глобальных шаблонов
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',  # Важно для django-tables2 и других
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database settings for PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('PG_DATABASE'),
        'USER': os.getenv('PG_USER'),
        'PASSWORD': os.getenv('PG_PASSWORD'),
        'HOST': os.getenv('PG_HOST', 'localhost'),
        'PORT': os.getenv('PG_PORT', '5432'),
    }
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 5,  # Минимум 5 символов вместо стандартных 8
        }
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Yekaterinburg')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Папка для дополнительных статических файлов (например, локальных)
STATICFILES_DIRS = [BASE_DIR / 'static']

# Папка, куда собираются все статики при collectstatic (для продакшна)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Медиа файлы (загрузка пользователями)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Логирование
LOGGING_DIR = BASE_DIR / 'logs'
LOGGING_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
        'file_errors': {
            'class': 'logging.FileHandler',
            'filename': LOGGING_DIR / 'django_error.log',
            'formatter': 'verbose',
            'level': 'ERROR',
            'encoding': 'utf-8',
        },
        'file_assignments': {
            'class': 'logging.FileHandler',
            'filename': LOGGING_DIR / 'assignments.log',
            'formatter': 'verbose',
            'level': 'INFO',
            'encoding': 'utf-8',
        },

    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'file_errors'],
            'level': 'ERROR',
            'propagate': False,
        },
        'shift_assignment': {
            'handlers': ['console', 'file_assignments'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Настройки почты
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@metallurg.ru'
IT_SUPPORT_EMAIL = 'it-support@metallurg.ru'  # или список адресов


