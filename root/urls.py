from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from root import settings

urlpatterns = (
        [
            path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
            path("", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
            path("admin/", admin.site.urls),
            path("api/v1/", include("apps.urls")),
        ]
        + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
