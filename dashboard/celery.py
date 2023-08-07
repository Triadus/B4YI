import os
from datetime import timedelta

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('dashboard')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # 'update_exchange_rates': {
    #     'task': 'dashboard.tasks.update_exchange_rates',
    #     'schedule': timedelta(minutes=1),
    #     # 'schedule': crontab(hour=3, minute=0, day_of_week='*'),  # Запуск каждый день в 03:00 UTC
    #     # 'schedule': crontab(hour=3, minute=0, timezone='UTC'),
    #     # 'schedule': crontab(minute=0, hour='*'),  # Запуск каждый час
    # },
    'calculate_total_balance': {
        'task': 'dashboard.tasks.calculate_total_balance',
        'schedule': timedelta(minutes=1),
        # 'schedule': crontab(hour=3, minute=0, day_of_week='*'),  # Запуск каждый день в 03:00 UTC
        # 'schedule': crontab(hour=3, minute=0, timezone='UTC'),
        # 'schedule': crontab(minute=0, hour='*'),  # Запуск каждый час
    },
}
