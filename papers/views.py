import requests
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode

from .models import SavedPaper, SearchHistory

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
    saved_ids = set(SavedPaper.objects.values_list("openalex_id", flat=True))

    if not query:
        return render(
            request,
            "papers/search.html",
            {"papers": [], "query": "", "saved_ids": saved_ids, "error": None},
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
                "saved_ids": saved_ids,
                "error": "Unable to reach the search service. Please try again later.",
            },
        )

    results = data.get("results") or []
    papers = [_extract_paper(w) for w in results]
    SearchHistory.objects.create(query=query)

    return render(
        request,
        "papers/search.html",
        {"papers": papers, "query": query, "saved_ids": saved_ids, "error": error},
    )


def save_paper_view(request):
    """Save a paper from search results. Redirects back to search."""
    if request.method != "POST":
        return redirect("search")

    openalex_id = request.POST.get("openalex_id", "").strip()
    if not openalex_id:
        return redirect("search")

    query = request.GET.get("q", "")
    redirect_url = reverse("search")
    if query:
        redirect_url += "?" + urlencode({"q": query})

    py = request.POST.get("publication_year", "").strip()
    try:
        publication_year = int(py) if py else None
    except ValueError:
        publication_year = None

    SavedPaper.objects.get_or_create(
        openalex_id=openalex_id,
        defaults={
            "title": (request.POST.get("title") or "Unknown")[:500],
            "first_author": request.POST.get("first_author") or None,
            "publication_year": publication_year,
            "cited_by_count": int(request.POST.get("cited_by_count") or 0),
        },
    )

    return redirect(redirect_url)


def unsave_paper_view(request):
    """Remove a saved paper. Redirects back to saved page."""
    if request.method != "POST":
        return redirect("saved")

    openalex_id = request.POST.get("openalex_id", "").strip()
    if openalex_id:
        SavedPaper.objects.filter(openalex_id=openalex_id).delete()

    return redirect("saved")


def saved_view(request):
    """List all saved papers at /saved/."""
    papers = SavedPaper.objects.all().order_by("-saved_at")
    return render(request, "papers/saved.html", {"papers": papers})
