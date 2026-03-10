from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("search/", views.search_view, name="search"),
    path("paper/<str:openalex_id>/", views.paper_detail_view, name="paper_detail"),
    path("save/", views.save_paper_view, name="save_paper"),
    path("unsave/", views.unsave_paper_view, name="unsave_paper"),
    path("saved/", views.saved_view, name="saved"),
    path("insights/", views.insights_view, name="insights"),
    path("api/search/", views.api_search_view, name="api_search"),
    path("api/paper/<str:openalex_id>/", views.api_paper_view, name="api_paper"),
    path("api/saved-papers/", views.api_saved_papers_view, name="api_saved_papers"),
    path("api/search-history/", views.api_search_history_view, name="api_search_history"),
    path("api/insights/", views.api_insights_view, name="api_insights"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
