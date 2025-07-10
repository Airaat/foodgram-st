from datetime import datetime

from django.http import FileResponse
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.filters import RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import (
    RecipeSerializer, ShortRecipeSerializer,
    IngredientSerializer
)
from recipes.models import (
    Recipe, Ingredient, ShoppingCart,
    Favorite, RecipeIngredient
)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if name:
            return self.queryset.filter(name__istartswith=name)
        return self.queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        auth_actions = {'create', 'favorite',
                        'shopping_cart', 'download_shopping_cart'}
        if self.action in auth_actions:
            return [IsAuthenticated()]
        elif self.action == 'get_link':
            return [AllowAny()]

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in {'favorite', 'shopping_cart'}:
            return ShortRecipeSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        params = self.request.query_params

        author = params.get('author')
        is_favorited = params.get('is_favorited')
        is_in_shopping_cart = params.get('is_in_shopping_cart')

        if author:
            queryset = queryset.filter(author__id=author)

        if user.is_authenticated:
            if is_favorited == '1':
                queryset = queryset.filter(favorited__user=user)
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(in_shopping_cart__user=user)

        return queryset

    def _post_delete_action(self, request, recipe, model):
        label_map = {
            'Favorite': 'в избранное',
            'ShoppingCart': 'в корзину покупок'
        }
        label = label_map.get(model.__name__, 'в список')

        if request.method == 'POST':
            obj, created = model.objects.get_or_create(
                user=request.user, recipe=recipe
            )

            if not created:
                data = {"errors": f"Рецепт «{recipe.name}» уже добавлен {label}."}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            context = {'request': request}
            serializer = ShortRecipeSerializer(recipe, context=context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        obj = model.objects.filter(user=request.user, recipe=recipe).first()
        if not obj:
            data = {"errors": f"Рецепт «{recipe.name}» не найден {label}."}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._post_delete_action(request, recipe, Favorite)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._post_delete_action(request, recipe, ShoppingCart)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total=Sum('amount')).order_by('ingredient__name')

        recipes = Recipe.objects.filter(in_shopping_cart__user=user)

        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        lines = [f'Список покупок — {timestamp}', '']

        for i, item in enumerate(ingredients, start=1):
            name = item["ingredient__name"].capitalize()
            unit = item["ingredient__measurement_unit"]
            amount = item["total"]
            lines.append(f"{i}. {name} ({unit}) — {amount}")

        lines.extend(['', 'Рецепты в списке покупок:', ''])
        for recipe in recipes:
            author = recipe.author.get_full_name() or recipe.author.username
            lines.append(f'— {recipe.name} (автор: {author})')

        content = '\n'.join(lines)
        return FileResponse(
            content,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain'
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        kwargs = {'recipe_id': pk}
        short_path = reverse('recipes:short-link-redirect', kwargs=kwargs)
        return Response({
            'short-link': request.build_absolute_uri(short_path)
        })
