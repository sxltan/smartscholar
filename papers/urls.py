from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("search/", views.search_view, name="search"),
    path("save/", views.save_paper_view, name="save_paper"),
    path("unsave/", views.unsave_paper_view, name="unsave_paper"),
    path("saved/", views.saved_view, name="saved"),
    path("insights/", views.insights_view, name="insights"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
