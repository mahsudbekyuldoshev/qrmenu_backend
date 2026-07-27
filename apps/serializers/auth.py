from django.contrib.auth.models import User
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.models.restaurants import Restaurant
from typing import Optional
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field


class UserSerializer(serializers.ModelSerializer):
    restaurant_id = serializers.SerializerMethodField()
    restaurant_slug = serializers.SerializerMethodField()
    restaurant_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "restaurant_id",
            "restaurant_slug",
            "restaurant_name",
        ]

    def _owned(self, obj):
        return obj.owned_restaurants.order_by("id").first()

    @extend_schema_field(OpenApiTypes.INT)
    def get_restaurant_id(self, obj: User) -> Optional[int]:
        restaurant = self._owned(obj)
        return restaurant.id if restaurant else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_restaurant_slug(self, obj: User) -> Optional[str]:
        restaurant = self._owned(obj)
        return restaurant.slug if restaurant else None

    @extend_schema_field(OpenApiTypes.STR)
    def get_restaurant_name(self, obj: User) -> Optional[str]:
        restaurant = self._owned(obj)
        return restaurant.name if restaurant else None



class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    restaurant_name = serializers.CharField(max_length=255)

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Bu email allaqachon roʻyxatdan oʻtgan.")
        return email

    def create(self, validated_data):
        email = validated_data["email"]
        full_name = validated_data.get("full_name", "").strip()
        restaurant_name = validated_data["restaurant_name"].strip()

        first_name = full_name
        last_name = ""
        if " " in full_name:
            first_name, last_name = full_name.split(" ", 1)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
        )

        base_slug = slugify(restaurant_name) or "restaurant"
        slug = base_slug
        i = 1
        while Restaurant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{i}"
            i += 1

        Restaurant.objects.create(
            name=restaurant_name,
            slug=slug,
            owner=user,
            is_active=True,
        )
        return user


class RestoFlowTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.EmailField(required=False)
        self.fields["username"].required = False

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        restaurant = user.owned_restaurants.order_by("id").first()
        if restaurant:
            token["restaurant_id"] = restaurant.id
            token["restaurant_slug"] = restaurant.slug
        return token

    def validate(self, attrs):
        email = self.initial_data.get("email")
        if email and not attrs.get(self.username_field):
            attrs[self.username_field] = str(email).lower().strip()
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
