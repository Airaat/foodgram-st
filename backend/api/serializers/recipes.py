from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Recipe, Ingredient, RecipeIngredient
from api.serializers.users import UserSerializer


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields

class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(many=True, write_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author',
            'ingredients', 'image', 'name', 'text', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['author'] = UserSerializer(instance.author, context=self.context).data
        representation['ingredients'] = RecipeIngredientReadSerializer(
            instance.recipe_ingredients.all(), many=True
        ).data
        request = self.context.get('request')
        representation['image'] = (
            request.build_absolute_uri(instance.image.url)
            if instance.image and request else None
        )
        return representation

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один ингредиент.')
        ids = [item['id'].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться.')
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Это поле обязательно.")
        return value

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and obj.favorited.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and obj.in_shopping_cart.filter(user=user).exists()

    def create_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ) for item in ingredients
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        super().update(instance, validated_data)
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(instance, ingredients)
        return instance

    def validate(self, attrs):
        if self.instance and self.context['request'].method in ('PUT', 'PATCH'):
            if 'ingredients' not in self.initial_data:
                raise serializers.ValidationError({
                    'ingredients': 'Нужен хотя бы один ингредиент.'
                })
        return super().validate(attrs)
