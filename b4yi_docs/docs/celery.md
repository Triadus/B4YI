## CELERY

## Установка

* `pip install celery` - Установка celery.
* `pip install redis` - Установка redis.


### Добавляем запись в файл  (__init.py__)


'from .celery import app as celery_app

__all__ = ('celery_app',)'

### Устанавливаем пакет если будут проблемы при запуске workera   

* `pip install eventlet`
* `celery -A worker -l info -P eventlet`

### Запуск worker

`celery -A wallets worker -l info -P eventlet`

### Запуск celery beat

`celery -A wallets beat -l info`