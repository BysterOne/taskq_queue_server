import os
import sys
from pathlib import Path
from typing import Any

import redis
import structlog
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from settings.logs import configure_logger

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
PROCESSING_ALIAS = os.getenv('PROCESSING_ALIAS', 'altyn')

HTTP_HOST = os.getenv('HTTP_HOST', 'http://localhost:8000')
DEBUG = int(os.environ.get('DEBUG', default=0))

if DEBUG:
    environment = 'dev'
else:
    environment = 'production'

if not SECRET_KEY:
    if environment == 'production':
        raise RuntimeError('DJANGO_SECRET_KEY environment variable is not set')
    SECRET_KEY = 'django-insecure-bxz$ouu)dtjz%s#_5**phuo-$#1tpielx7n0$2vzfx627hk$qm'

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    HTTP_HOST,
    'http://127.0.0.1',
    'http://127.0.0.1:8000',
    'http://localhost',
    'http://0.0.0.0',
]

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

EXTERNAL_APPS = [
    'corsheaders',
    'django_structlog',
    'cacheops',
    'djangoql',
    'prettyjson',
    'admin_auto_filters',
    'rest_framework',
    'health_check',
    'health_check.db',
    'health_check.contrib.migrations',
    'health_check.contrib.redis',
]

MY_APPS = [
    'apps.core',
]

INSTALLED_APPS = DJANGO_APPS + EXTERNAL_APPS + MY_APPS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('PSQL_NAME', 'psql'),
        'HOST': os.getenv('PSQL_HOST', 'psql'),
        'PORT': os.getenv('PSQL_PORT', '5432'),
        'USER': os.getenv('PSQL_USER', 'psql'),
        'PASSWORD': os.getenv('PSQL_PASS', 'pass'),
    },
}

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_PASS = os.getenv('REDIS_PASS', None)
REDIS_DB_CACHE = 3

CACHES = {
    # needed for DRF rate limiting, otherwise unused
    # ask @Barsoomx if need to migrate to redis sentinel in the future
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'KEY_PREFIX': 'caching:django',
        'LOCATION': f'redis://:{REDIS_PASS}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CACHE}',
    },
}
REDIS_URL = f'redis://:{REDIS_PASS}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CACHE}'  # used only in RedisHealthCheck

CACHEOPS_REDIS = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'password': REDIS_PASS,
    'db': 0,
    'retry_on_error': [redis.exceptions.ConnectionError, redis.exceptions.TimeoutError],
    'retry': Retry(ExponentialBackoff(), 3),
}
CACHEOPS_DEGRADE_ON_FAILURE = True


# noinspection PyPep8Naming
def CACHEOPS_PREFIX(_: Any) -> str:  # noqa: N802
    return f'altyn:cacheops:{environment}:'


CACHEOPS = {
    'django.content_type': {'ops': ('fetch',), 'timeout': 60},
    'auth.group.permissions': {'ops': ('fetch',), 'timeout': 60 * 2},
    'auth.permission': {'ops': ('fetch',), 'timeout': 60 * 2},
}

HEALTH_CHECK = {
    'SUBSETS': {
        'readyz': [
            'MigrationsHealthCheck',
        ],
        'healthz': [],
        'startup': [
            'DatabaseBackend',
        ],
    },
}

MIDDLEWARE = [
    'apps.core.middlewares.monitoring.RequestTimingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middlewares.DRFAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middlewares.monitoring.UserLogMiddleware',
    'apps.core.middlewares.monitoring.EventContextMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
    'apps.core.middlewares.ExceptionHandlingMiddleware',
    'apps.core.auth.middleware.UpdateClientSessionMiddleware',
]

ROOT_URLCONF = 'settings.urls'

# noinspection PyUnresolvedReferences
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'settings.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_CLASSES = [
    'apps.core.auth.authentication.ClientSessionAuthentication',
]

# noinspection PyUnresolvedReferences
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.middlewares.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.core.auth.authentication.ClientSessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'apps.core.auth.authentication.IsPhoneVerified',
        'apps.core.auth.authentication.IsPinVerified',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'burst': '60/min',
        'sustained': '1000/day',
    },
}

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = os.getenv('DJANGO_STATIC_URL', '/static/')
STATIC_ROOT = BASE_DIR.parent / 'public' / 'static'
if DEBUG:
    STATIC_URL = '/static/'

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = ('*',)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ('*',)

LOG_FORMATTER = os.environ.get('LOG_FORMATTER', 'console')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'json': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
        },
        'console': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.dev.ConsoleRenderer(),
        },
    },
    'handlers': {
        'console_debug': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': LOG_FORMATTER,
            'filters': ['require_debug_true'],
            'stream': sys.stdout,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': LOG_FORMATTER,
            'level': 'INFO',
            'stream': sys.stdout,
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console_debug'],
        },
        '': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['console_debug'] if DEBUG else ['console'],
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

configure_logger(log_level='DEBUG' if DEBUG else 'INFO', env_profile=environment)

MONITORING_STATSD_HOST = os.getenv('MONITORING_STATSD_HOST', 'statsd-exporter')
MONITORING_STATSD_PORT = 9125

DJANGO_STRUCTLOG_CELERY_ENABLED = True
PROCESSING_KEY_ENCRYPTION_SECRET = os.getenv('PROCESSING_KEY_ENCRYPTION_SECRET')

GENESIS_API_LOGIN = os.getenv('GENESIS_API_LOGIN')
GENESIS_API_PASSWORD = os.getenv('GENESIS_API_PASSWORD')

ALTYN_LOGO = "https://storage.yandexcloud.net/lk-altyn-media/altyn_logo.png"
