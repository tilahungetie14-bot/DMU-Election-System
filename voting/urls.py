from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("register/", views.register, name="register"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("election/<int:election_id>/vote/", views.ballot, name="ballot"),
    path("election/<int:election_id>/cast/", views.cast_vote, name="cast_vote"),
    path("election/<int:election_id>/results/", views.results, name="results"),
]
