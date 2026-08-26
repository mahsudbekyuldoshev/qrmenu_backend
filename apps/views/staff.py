from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.models.users import User
from apps.permission import IsRestaurantDirectorOrManager
from apps.serializers.staff import StaffCreateSerializer, StaffSerializer

# Har bir rol qaysi rollarni "ko'rishi" (ro'yxatda) mumkinligi.
VISIBLE_ROLES_BY_VIEWER = {
    User.Role.DIRECTOR: (User.Role.MANAGER, User.Role.WAITER, User.Role.CHEF),
    User.Role.MANAGER: (User.Role.WAITER, User.Role.CHEF),
}


@extend_schema_view(
    list=extend_schema(tags=["Staff"]),
    retrieve=extend_schema(tags=["Staff"]),
    create=extend_schema(
        tags=["Staff"],
        request=StaffCreateSerializer,
        responses={201: StaffSerializer},
    ),
    update=extend_schema(tags=["Staff"]),
    partial_update=extend_schema(tags=["Staff"]),
    destroy=extend_schema(tags=["Staff"]),
)
class StaffViewSet(ModelViewSet):
    """
    Director/Manager o'z restoranidagi xodimlarni yaratadi/ko'radi/
    tahrirlaydi/o'chiradi.

    - Director: manager + waiter + chef larni ko'radi/yaratadi/boshqaradi.
    - Manager: faqat waiter + chef larni ko'radi/yaratadi/boshqaradi
      (boshqa managerlarga yoki directorga tega olmaydi).

    PATCH orqali `employment_status` o'zgartirilganda (fired/resigned),
    xodim avtomatik `is_active=False` bo'lib, tizimga kira olmay qoladi.
    DELETE - hisobni butunlay o'chiradi (tarixiy yozuv kerak bo'lsa, buning
    o'rniga employment_status='fired'/'resigned' qo'yish tavsiya etiladi).
    """

    permission_classes = (IsAuthenticated, IsRestaurantDirectorOrManager)

    def get_serializer_class(self):
        return StaffCreateSerializer if self.action == "create" else StaffSerializer

    def get_queryset(self):
        user = self.request.user
        visible_roles = VISIBLE_ROLES_BY_VIEWER.get(user.role, ())
        return User.objects.filter(
            restaurant=user.restaurant, role__in=visible_roles
        ).order_by("-date_joined")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        new_user = serializer.save()

        response_data = StaffSerializer(new_user).data
        # Agar parol admin tomonidan berilmay, tizim tomonidan generatsiya
        # qilingan bo'lsa - FAQAT shu bir martalik javobda ko'rsatamiz.
        generated = getattr(new_user, "_generated_password", None)
        if generated:
            response_data["generated_password"] = generated
        return Response(response_data, status=status.HTTP_201_CREATED)