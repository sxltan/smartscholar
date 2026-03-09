from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("search/", views.search_view, name="search"),
    path("save/", views.save_paper_view, name="save_paper"),
    path("unsave/", views.unsave_paper_view, name="unsave_paper"),
    path("saved/", views.saved_view, name="saved"),
]
