from django.urls import path

from assistant import views

urlpatterns = [
    path("auction/bid_assistant/<int:auction_id>", views.bid_assistant, name="bid_assistant"),
    path("auction/assistant_info", views.assistant_info, name="assistant_info"),
    path("auction/bid_assistant/details/<int:auction_id>", views.bid_assistant_details, name="bid_assistant_details"),
    path("auction/bid_assistant/edit/<int:auction_id>", views.bid_assistant_update, name="bid_assistant_update"),
    path("auction/bid_assistant/delete/<int:auction_id>", views.bid_assistant_delete, name="bid_assistant_delete"),
    path("notifications", views.get_notification, name="notifications"),
]
