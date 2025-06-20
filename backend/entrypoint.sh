#!/bin/bash

# Применяем миграции
python manage.py migrate --noinput

# Собираем статику
python manage.py collectstatic --noinput

# Запускаем сервер
gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
