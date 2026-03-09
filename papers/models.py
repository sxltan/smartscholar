from django.db import models


class SearchHistory(models.Model):
    query = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.query} ({self.searched_at})"


class SavedPaper(models.Model):
    title = models.CharField(max_length=500)
    openalex_id = models.CharField(max_length=100, unique=True)
    first_author = models.CharField(max_length=255, blank=True, null=True)
    publication_year = models.IntegerField(blank=True, null=True)
    cited_by_count = models.IntegerField(default=0)
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
