from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path("", include("auctions.urls")),
    path("", include("payment.urls")),
    path("", include("assistant.urls")),
]
