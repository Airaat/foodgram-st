from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.recipes import RecipeViewSet, IngredientViewSet
from api.views.users import UserViewSet

router = DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
