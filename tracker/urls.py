from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.load_signup, name="signup"),
    path("login/", views.load_login, name="login"),
    path("logout/", views.attempt_logout, name="logout"),
    path("strava_callback/", views.strava_callback, name="strava_callback"),
    path("account/", views.account, name="account"),
    path("link_strava/", views.link_strava, name="link_strava"),
    path("unlink_strava/", views.unlink_strava, name="unlink_strava"),
    path("delete_account/", views.delete_account, name="delete_account"),
    path("leaderboard/", views.leaderboard_page, name="leaderboard"),
    path("user/", views.user, name="user"),
    path("user/stats/", views.stats, name="stats"),
    path("user/milestones/", views.milestones, name="milestones"),
    path("user/altitudes/", views.altitude_milestones, name="altitude_milestones"),
    path("trophies/", views.trophies, name="trophies")
]