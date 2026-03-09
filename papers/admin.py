from django.contrib import admin

from .models import SavedPaper, SearchHistory

admin.site.register(SearchHistory)
admin.site.register(SavedPaper)
