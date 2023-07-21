# -*- coding: utf-8 -*-
import os

from pathlib import Path

from dotenv import load_dotenv

env_path = Path('.') / '.env'

load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent.parent
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ['*']
# CSRF_TRUSTED_ORIGINS = ['https://8192-185-219-71-82.ngrok-free.app']

DB_ENGINE = os.getenv('DB_ENGINE', None)
DB_USERNAME = os.getenv('DB_USERNAME', None)
DB_PASS = os.getenv('DB_PASS', None)
DB_HOST = os.getenv('DB_HOST', None)
DB_PORT = os.getenv('DB_PORT', None)
DB_NAME = os.getenv('DB_NAME', None)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + DB_ENGINE,
        'NAME': DB_NAME,
        'USER': DB_USERNAME,
        'PASSWORD': DB_PASS,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, "static")
