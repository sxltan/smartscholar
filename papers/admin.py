from django.contrib import admin

from .models import SavedPaper, SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ["query", "user", "searched_at"]
    list_filter = ["user"]


@admin.register(SavedPaper)
class SavedPaperAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "openalex_id", "saved_at"]
    list_filter = ["user"]
