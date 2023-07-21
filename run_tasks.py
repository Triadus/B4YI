import os

import django
from django.contrib.auth.models import User
from dashboard.tasks import update_exchange_rates

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
update_exchange_rates()
