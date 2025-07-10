import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из JSON-файла'

    def handle(self, *args, **kwargs):
        file_path = Path(settings.BASE_DIR) / 'data' / 'ingredients.json'
        try:
            with open(file_path, encoding='utf-8') as f:
                ingredients_data = json.load(f)

            existing = set(
                Ingredient.objects.values_list('name', 'measurement_unit')
            )
            new_ingredients = [
                Ingredient(**elem)
                for elem in ingredients_data
                if (elem['name'], elem['measurement_unit']) not in existing
            ]

            if not new_ingredients:
                self.stdout.write(self.style.SUCCESS(
                    'Нет новых ингредиентов для добавления.'
                ))
                return

            with transaction.atomic():
                created = Ingredient.objects.bulk_create(
                    new_ingredients,
                    ignore_conflicts=True
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Добавлено {len(created)} новых ингредиентов.'
                ))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'Файл не найден: {file_path}'
            ))
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка распаковки JSON: {e}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка импорта: {e}'
            ))
