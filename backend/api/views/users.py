import base64

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.db.models import Count
from djoser.serializers import UserCreateSerializer, SetPasswordSerializer

from api.serializers.users import (
    UserSerializer,
    SubscriptionUserSerializer
)
from api.pagination import CustomPagination
from recipes.models import Subscription

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

    def get_permissions(self):
        auth_actions = {'me', 'avatar', 'subscribe',
                        'subscriptions', 'set_password'}
        if self.action in auth_actions:
            return [IsAuthenticated()]

        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def _avatar_update(self, user, avatar_data):
        try:
            user.avatar = Base64ImageField().to_internal_value(avatar_data)
            user.save()

            with user.avatar.open("rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                ext = user.avatar.name.split('.')[-1]
                mime = f"image/{ext if ext != 'jpg' else 'jpeg'}"
                avatar_response = f"data:{mime};base64,{encoded}"

            return Response({'avatar': avatar_response})
        except Exception:
            return Response(
                {'error': 'Невалидный формат изображения'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'error': 'Аватар не был передан'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return self._avatar_update(user, avatar_data)

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user
        subscription_exists = Subscription.objects.filter(
            user=user, author=author
        )

        if request.method == 'POST':
            if subscription_exists:
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionUserSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not subscription_exists:
            return Response(
                {"errors": "Вы не были подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(subscribers__user=user).annotate(
            recipes_count=Count('recipes')
        )
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionUserSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
