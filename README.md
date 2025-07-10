# Foodgram - Финальный проект для yandex.practicum

## Подготовка проекта
1. Создайте файл `infra/.env`
2. Заполните согласно примеру ниже:
```
DB_HOST=db
DB_PORT=5432
POSTGRES_DB=name_db
POSTGRES_USER=name_user
POSTGRES_PASSWORD=password
SECRET_KEY=your_secret_key
DEBUG=True
```

## Запуск
Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.
```shell
  docker compose up
```

Приложение доступно по адресу http://localhost

## Заполнение базы данных
Для корректной работы приложения, нужно заполнить таблицу "Ингредиенты" данными, для этого выполните команду:
```shell
  docker exec -it foodgram-backend python manage.py loadingredients
```
