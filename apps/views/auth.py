from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.serializers.auth import (
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    RestoFlowTokenObtainPairSerializer,
    UserSerializer,
)


@extend_schema(tags=["Auth"])
class LoginView(TokenObtainPairView):
    """Telefon raqam + parol orqali login (RestoFlowTokenObtainPairSerializer)."""

    serializer_class = RestoFlowTokenObtainPairSerializer
    permission_classes = ()


@extend_schema(tags=["Auth"])
class MeView(GenericAPIView):
    """GET/PATCH /auth/me/ — joriy foydalanuvchi profili."""

    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return ProfileUpdateSerializer
        return UserSerializer

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=ProfileUpdateSerializer, responses=UserSerializer)
    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=ProfileUpdateSerializer, responses=UserSerializer)
    def put(self, request):
        return self.patch(request)


@extend_schema(tags=["Auth"])
class ChangePasswordView(GenericAPIView):
    """
    POST /auth/change-password/  body: {old_password, new_password}
    Har qanday login qilgan foydalanuvchi uchun ochiq.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: OpenApiResponse(description="Parol muvaffaqiyatli o'zgartirildi.")},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Parol muvaffaqiyatli o'zgartirildi."})