from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("user/", views.user, name="user"),
    path("user/milestones/", views.milestones, name="milestones"),
    path("trophies/", views.trophies, name="trophies")
]