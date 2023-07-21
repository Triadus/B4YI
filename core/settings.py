# -*- coding: utf-8 -*-
import os

from pathlib import Path

from dotenv import load_dotenv

env_path = Path('.') / '.env'

load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'dashboard',

    'crispy_forms',
    'crispy_bootstrap4',

    'allauth',
    'allauth.account',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

HOME_TEMPLATES = os.path.join(BASE_DIR, 'templates')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [HOME_TEMPLATES],
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

WSGI_APPLICATION = 'core.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en'

TIME_ZONE = 'Europe/Sofia'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Авторизация

SITE_ID = 1

# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         # For each OAuth based provider, either add a ``SocialApp``
#         # (``socialaccount`` app) containing the required client
#         # credentials, or list them here:
#         'APP': {
#             'client_id': '123',
#             'secret': '456',
#             'key': ''
#         }
#     }
# }

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'account_login'

ACCOUNT_SIGNUP_REDIRECT_URL = "account_logout"
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

ACCOUNT_FORMS = {
    'login': 'dashboard.forms.UserLoginForm',
    'signup': 'dashboard.forms.UserRegistrationForm',
    'change_password': 'dashboard.forms.PasswordChangeForm',
    'set_password': 'dashboard.forms.PasswordSetForm',
    'reset_password': 'dashboard.forms.PasswordResetForm',
    'reset_password_from_key': 'dashboard.forms.PasswordResetKeyForm'
}

# Настройка сессий и длительности cookies

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60  # кратное 60 секунд
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# SESSION_COOKIE_SECURE = False

# Настройки почты

EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tegro.od.ua@gmail.com'
EMAIL_HOST_PASSWORD = EMAIL_PASSWORD
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Отправка писем администратору , работает только при выключенном DEBUG=False
EMAIL_ADMIN = os.getenv('EMAIL_ADMIN')
ADMINS = [("Maximus", EMAIL_ADMIN)]
EMAIL_SUBJECT_PREFIX = '[B4YI] '

# Настройка Redis

REDIS_HOST = '192.168.146.130'
REDIS_PORT = '6379'
CELERY_BROKER_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# # Запуск Celery при загрузке приложения
# CELERY_APP_NAME = 'your_project_name'
# CELERY_IMPORTS = [
#     'your_app_name.tasks',
# ]

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

try:
    from .local_settings import *
except ImportError:
    from .prod_settings import *
