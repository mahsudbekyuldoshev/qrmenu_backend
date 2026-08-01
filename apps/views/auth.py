from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.models import User
from apps.serializers.auth import (
    RegisterSerializer,
    RestoFlowTokenObtainPairSerializer,
    UserSerializer,
)


class RegisterView(CreateAPIView):
    """
    Faqat Ofitsiant/Oshpaz shu orqali ro'yxatdan o'tadi (RegisterSerializer'da
    role WAITER/CHEF bilan cheklangan). Manager/Super Admin hisoblari bu yerdan
    yaratilmaydi — ular Super Admin panel orqali yaratiladi (qarang: admin.py).
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RestoFlowTokenObtainPairSerializer.get_token(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Telefon raqam + parol orqali login (RestoFlowTokenObtainPairSerializer)."""

    serializer_class = RestoFlowTokenObtainPairSerializer
    permission_classes = (AllowAny,)


class MeView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        return Response(self.get_serializer(request.user).data)
