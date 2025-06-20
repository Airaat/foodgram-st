from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, SetPasswordSerializer

import base64


from api.serializers.users import (
    UserSerializer,
    SubscriptionUserSerializer
)
from api.pagination import CustomPagination
from recipes.models import Subscription
from api.serializers.recipes import ShortRecipeSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPagination
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar', permission_classes=[IsAuthenticated])
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response({'error': 'Аватар не был передан'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                field = Base64ImageField()
                user.avatar = field.to_internal_value(avatar_data)
                user.save()

                with user.avatar.open("rb") as f:
                    encoded = base64.b64encode(f.read()).decode('utf-8')
                    ext = user.avatar.name.split('.')[-1]
                    mime = f"image/{ext if ext != 'jpg' else 'jpeg'}"
                    avatar_response = f"data:{mime};base64,{encoded}"

                return Response({'avatar': avatar_response}, status=status.HTTP_200_OK)
            except Exception:
                return Response({'error': 'Невалидный формат изображения'}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя."},
                    status=400
                )

            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя."},
                    status=400
                )

            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionUserSerializer(author, context={'request': request})
            return Response(serializer.data, status=201)

        deleted, _ = Subscription.objects.filter(user=user, author=author).delete()
        if deleted:
            return Response(status=204)
        return Response(
            {"errors": "Вы не были подписаны на этого пользователя."},
            status=400
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(subscribers__user=user).annotate(
            recipes_count=Count('recipes')
        )
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionUserSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
