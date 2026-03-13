from django.test import TestCase
from django.urls import reverse

from papers.views import _validate_search_params


class PapersTestCase(TestCase):
    def test_validate_search_params_missing_query_returns_error(self):
        """_validate_search_params returns an error when the query is missing."""
        error, _, _ = _validate_search_params("", "", "")
        self.assertIsNotNone(error)
        self.assertIn("Query", error)

    def test_validate_search_params_converts_valid_years(self):
        """_validate_search_params correctly converts valid year values."""
        error, from_year_int, to_year_int = _validate_search_params("test", "2020", "2022")
        self.assertIsNone(error)
        self.assertEqual(from_year_int, 2020)
        self.assertEqual(to_year_int, 2022)

    def test_api_saved_papers_returns_401_when_not_authenticated(self):
        """api_saved_papers endpoint returns 401 when the user is not authenticated."""
        url = reverse("api_saved_papers")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_api_search_returns_400_when_query_missing(self):
        """api_search returns HTTP 400 if the query parameter is missing."""
        url = reverse("api_search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
