from django.urls import path
from .views import (
    health_check,
    short_link_redirect_view,
)

app_name = 'recipes'

urlpatterns = [
    path('health', health_check, name='health-check'),
    path('<int:recipe_id>/', short_link_redirect_view, name='short-link-redirect'),
]
