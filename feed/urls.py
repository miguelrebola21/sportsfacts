from django.urls import path

from . import views

app_name = "feed"

urlpatterns = [
    path("", views.home, name="home"),
    path("vote/<str:item_type>/<int:item_id>/<str:direction>/", views.vote, name="vote"),
    path("share/<str:item_type>/<int:item_id>.png", views.share_image, name="share_image"),
]
