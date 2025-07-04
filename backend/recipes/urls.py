from django.urls import path
from .views import short_link_redirect_view

app_name = 'recipes'

urlpatterns = [
    path('<int:recipe_id>/', short_link_redirect_view, name='short-link-redirect'),
]
