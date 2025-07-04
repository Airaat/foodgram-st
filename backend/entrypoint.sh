#!/bin/bash

# Применяем миграции
python manage.py migrate --noinput

# Собираем статику
python manage.py collectstatic --noinput

# Заполняем базу данных
python manage.py import_ingredients

# Запускаем сервер
gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
