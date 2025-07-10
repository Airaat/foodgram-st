from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from .models import Recipe, Ingredient, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_range'
    STATIC_RANGES = [
        ('fast', 'Быстрые (<30 мин)'),
        ('medium', 'Средние (30-60 мин)'),
        ('slow', 'Долгие (>60 мин)'),
    ]

    def lookups(self, request, model_admin):
        return self.STATIC_RANGES

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'fast':
            return queryset.filter(cooking_time__lt=30)
        if value == 'medium':
            return queryset.filter(cooking_time__range=(30, 60))
        if value == 'slow':
            return queryset.filter(cooking_time__gt=60)
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
            return mark_safe(
                '<img src="{}" width="80" height="80" style="object-fit: cover;" />'
                .format(recipe.image.url)
            )
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
