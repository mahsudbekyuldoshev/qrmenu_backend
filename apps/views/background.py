import requests
from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, IntegerField
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from apps.permission import IsRestaurantManagerOnly

UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


class BackgroundSearchView(APIView):
    """
    GET /api/v1/manager/backgrounds/search/?q=uzbek+restaurant&page=1

    Manager panelidagi "Rasm qidirish" tugmasi endi Google'ga emas, shu
    endpointga murojaat qiladi. Unsplash API kaliti faqat SERVERDA saqlanadi
    (frontend'ga hech qachon ochilmaydi) - shuning uchun bu APIView orqali
    "proksi" qilinadi.

    Natijada faqat BEPUL, litsenziyasiz (royalty-free) rasmlar qaytadi -
    Google Images'dagi kabi Shutterstock/Adobe Stock litsenziyalangan
    rasmlar EMAS (ularni ruxsatsiz ishlatish mualliflik huquqini buzadi).
    """

    permission_classes = (IsAuthenticated, IsRestaurantManagerOnly)

    def get(self, request):
        query = request.query_params.get("q", "restaurant interior")
        page = request.query_params.get("page", 1)

        if not settings.UNSPLASH_ACCESS_KEY:
            return Response(
                {"detail": "UNSPLASH_ACCESS_KEY sozlanmagan (.env faylni tekshiring)."},
                status=503,
            )

        response = requests.get(
            UNSPLASH_SEARCH_URL,
            params={
                "query": query,
                "page": page,
                "per_page": 12,
                "orientation": "portrait",
            },
            headers={"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"},
            timeout=10,
        )

        if not response.ok:
            return Response(
                {"detail": "Rasm qidiruv xizmati vaqtincha ishlamayapti."},
                status=502,
            )

        data = response.json()
        results = [
            {
                "id": item["id"],
                "thumb_url": item["urls"]["small"],
                "full_url": item["urls"]["regular"],
                "photographer": item["user"]["name"],
                "photographer_url": item["user"]["links"]["html"],
            }
            for item in data.get("results", [])
        ]
        return Response({"results": results, "total_pages": data.get("total_pages", 1)})


class BackgroundSelectSerializer(Serializer):
    image_url = CharField()
    unsplash_id = CharField(required=False, allow_blank=True)


class BackgroundSelectView(APIView):
    """
    POST /api/v1/manager/backgrounds/select/
    body: {"image_url": "https://images.unsplash.com/...", "unsplash_id": "abc123"}

    Manager qidiruv natijasidan bitta rasmni tanlaydi. Frontend hech qanday
    faylni o'zi yuklamaydi/qayta yubormaydi - faqat tanlangan rasmning
    URL'ini yuboradi. Rasmni haqiqiy yuklab olish va `menu_background`ga
    saqlash ISHI SERVERDA bajariladi.
    """

    permission_classes = (IsAuthenticated, IsRestaurantManagerOnly)

    def post(self, request):
        serializer = BackgroundSelectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_url = serializer.validated_data["image_url"]

        restaurant = request.user.restaurant
        if restaurant is None:
            raise ValidationError("Sizga tegishli restoran topilmadi.")

        try:
            image_response = requests.get(image_url, timeout=15)
            image_response.raise_for_status()
        except requests.RequestException:
            raise ValidationError("Rasmni yuklab olishda xatolik yuz berdi.")

        content_type = image_response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            raise ValidationError("Berilgan URL rasm emas.")

        file_name = (
            f"{serializer.validated_data.get('unsplash_id') or 'background'}.jpg"
        )
        restaurant.menu_background.save(
            file_name, ContentFile(image_response.content), save=True
        )

        return Response(
            {
                "menu_background": request.build_absolute_uri(
                    restaurant.menu_background.url
                )
            }
        )
