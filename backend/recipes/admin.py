from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from .models import (
    Recipe, Ingredient, RecipeIngredient,
    Favorite, ShoppingCart, Subscription
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_range'

    def lookups(self, request, model_admin):
        times = sorted(set(Recipe.objects.values_list('cooking_time', flat=True)))
        if len(times) < 3:
            return ()

        self.n = times[int(len(times) * 0.33)]
        self.m = times[int(len(times) * 0.66)]

        return [
            ('lt', f'Меньше {self.n} мин ({Recipe.objects.filter(cooking_time__lt=self.n).count()})'),
            ('range', f'От {self.n} до {self.m} мин ({Recipe.objects.filter(cooking_time__gte=self.n, cooking_time__lte=self.m).count()})'),
            ('gt', f'Больше {self.m} мин ({Recipe.objects.filter(cooking_time__gt=self.m).count()})'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'lt':
            return queryset.filter(cooking_time__lt=self.n)
        if value == 'range':
            return queryset.filter(cooking_time__gte=self.n, cooking_time__lte=self.m)
        if value == 'gt':
            return queryset.filter(cooking_time__gt=self.m)
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author',
        'show_favorites_count', 'show_ingredients', 'show_image'
    )
    search_fields = ('name', 'author__username')
    list_filter = ('author', CookingTimeFilter)
    inlines = [RecipeIngredientInline]
    readonly_fields = ('show_favorites_count', 'show_image')

    @admin.display(description='В избранном')
    def show_favorites_count(self, recipe):
        return recipe.favorited_by.count()

    @admin.display(description='Ингредиенты')
    def show_ingredients(self, recipe):
        return format_html('<br>'.join(
            f'{ri.ingredient.name} ({ri.amount}{ri.ingredient.measurement_unit})'
            for ri in recipe.recipe_ingredients.all()
        ))

    @admin.display(description='Картинка')
    def show_image(self, recipe):
        if recipe.image:
            return mark_safe(f'<img src="{recipe.image.url}" width="80" height="80" style="object-fit: cover;" />')
        return '—'


class HasRecipesFilter(SimpleListFilter):
    title = 'Наличие в рецептах'
    parameter_name = 'has_recipes'

    LOOKUPS = (
        ('yes', 'Используются'),
        ('no', 'Не используются'),
    )

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipe__isnull=False).distinct()
        elif self.value() == 'no':
            return queryset.filter(recipe__isnull=True)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', HasRecipesFilter)

    @admin.display(description='Рецептов')
    def recipes_count(self, ingredient):
        return ingredient.ingredient_recipes.count()
