import requests
from django.shortcuts import render

OPENALEX_WORKS_URL = "https://api.openalex.org/works"


def _extract_paper(work):
    """Extract a clean subset of fields from an OpenAlex work object."""
    first_author = None
    authorships = work.get("authorships") or []
    for a in authorships:
        if a.get("author_position") == "first":
            author_obj = a.get("author")
            if author_obj:
                first_author = author_obj.get("display_name")
            break

    return {
        "title": work.get("title") or work.get("display_name") or "Unknown",
        "publication_year": work.get("publication_year"),
        "cited_by_count": work.get("cited_by_count", 0),
        "first_author": first_author,
        "openalex_id": work.get("id"),
    }


def home_view(request):
    """Homepage at /."""
    return render(request, "papers/home.html")


def search_view(request):
    """Search papers at /search/ using query parameter q."""
    query = request.GET.get("q", "").strip()
    papers = []
    error = None

    if not query:
        return render(
            request,
            "papers/search.html",
            {"papers": [], "query": "", "error": "Please enter a search term."},
        )

    try:
        response = requests.get(
            OPENALEX_WORKS_URL,
            params={"search": query, "per_page": 10},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return render(
            request,
            "papers/search.html",
            {
                "papers": [],
                "query": query,
                "error": "Unable to reach the search service. Please try again later.",
            },
        )

    results = data.get("results") or []
    papers = [_extract_paper(w) for w in results]

    return render(
        request,
        "papers/search.html",
        {"papers": papers, "query": query, "error": error},
    )
