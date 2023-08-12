# -*- coding: utf-8 -*-
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path('.') / '.env'

load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent.parent
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = ['*']
# CSRF_TRUSTED_ORIGINS = ['https://8192-185-219-71-82.ngrok-free.app']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'b4youi',
        'USER': 'triadus',
        'PASSWORD': 'triadus',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


STATIC_ROOT = os.path.join(BASE_DIR, "static")
