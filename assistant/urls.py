from django.urls import path

from assistant import views

urlpatterns = [
    path("auction/bid_assistant/<int:auction_id>", views.bid_assistant, name="bid_assistant"),
    path("auction/assistant_info", views.assistant_info, name="assistant_info"),
]
