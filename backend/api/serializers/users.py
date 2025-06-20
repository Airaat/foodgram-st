from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.contrib.auth import get_user_model
from recipes.models import Subscription

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        ]
        read_only_fields = fields

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(user=request.user, author=user).exists()


class SubscriptionUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar',
            'recipes', 'recipes_count'
        )
        read_only_fields = fields

    def get_recipes(self, user):
        from api.serializers.recipes import ShortRecipeSerializer
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = user.recipes.all()
        if recipes_limit and recipes_limit.strip().isdigit():
            recipes = recipes[:int(recipes_limit.strip())]
        return ShortRecipeSerializer(recipes, many=True, context={'request': request}).data
