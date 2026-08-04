from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.serializers.auth import (
    ChangePasswordSerializer,
    RestoFlowTokenObtainPairSerializer,
    UserSerializer,
)

# TUZATISH: RegisterView OLIB TASHLANDI. Endi ochiq ro'yxatdan o'tish yo'q -
# barcha hisoblar ierarxik tarzda yaratiladi:
#   super_admin -> director (apps.views.admin.DirectorViewSet)
#   director/manager -> manager/waiter/chef (apps.views.staff.StaffViewSet)


class LoginView(TokenObtainPairView):
    """Telefon raqam + parol orqali login (RestoFlowTokenObtainPairSerializer)."""

    serializer_class = RestoFlowTokenObtainPairSerializer
    permission_classes = ()


class MeView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        return Response(self.get_serializer(request.user).data)


class ChangePasswordView(GenericAPIView):
    """
    POST /auth/change-password/  body: {old_password, new_password}
    Har qanday login qilgan foydalanuvchi uchun ochiq.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Parol muvaffaqiyatli o'zgartirildi."})