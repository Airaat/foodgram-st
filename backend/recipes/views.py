from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipe


def short_link_redirect_view(request, recipe_id):
    """
    Обрабатывает короткую ссылку и перенаправляет на полную.
    """

    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe_id}/')


def health_check(request):
    return JsonResponse({'status': 'ok'})
