# Добро пожаловать в B4YI


## Установка

* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Вспомогательные функции --

### Пакет для создания зависимостей
  `pip install pipreqs`

* `pipreqs` - Создание файла зависимостей.
* `pipreqs --encoding utf-8 --force` - если выдает ошибку

### Команды для миграций
    python manage.py migrate app zero --fake    # обновление миграций

    (virtualenv)python manage.py makemigrations
    (virtualenv)python manage.py migrate --fake
    (virtualenv)python manage.py migrate
    
