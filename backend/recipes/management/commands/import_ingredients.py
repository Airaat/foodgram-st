import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из JSON-файла'

    def handle(self, *args, **kwargs):
        try:
            filepath = os.path.normpath(os.path.join(settings.BASE_DIR, 'data', 'ingredients.json'))
            with open(filepath, encoding='utf-8') as f:
                existing = set(
                    Ingredient.objects.values_list('name', 'measurement_unit')
                )
                new_ingredients = [
                    Ingredient(**item)
                    for item in json.load(f)
                    if (item['name'], item['measurement_unit']) not in existing
                ]
                created = Ingredient.objects.bulk_create(new_ingredients, ignore_conflicts=True)
                self.stdout.write(
                    self.style.SUCCESS(f'Добавлено {len(created)} новых ингредиентов.')
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка импорта: {e}'))
