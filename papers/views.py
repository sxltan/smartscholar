import requests
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
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

    if request.user.is_authenticated:
        saved_ids = set(
            SavedPaper.objects.filter(user=request.user).values_list(
                "openalex_id", flat=True
            )
        )
    else:
        saved_ids = set()

    login_next = reverse("search")
    if query:
        login_next += "?" + urlencode({"q": query})

    if not query:
        return render(
            request,
            "papers/search.html",
            {"papers": [], "query": "", "saved_ids": saved_ids, "error": None, "login_next": login_next},
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
                "login_next": login_next,
            },
        )

    results = data.get("results") or []
    papers = [_extract_paper(w) for w in results]

    if request.user.is_authenticated:
        SearchHistory.objects.create(user=request.user, query=query)

    return render(
        request,
        "papers/search.html",
        {"papers": papers, "query": query, "saved_ids": saved_ids, "error": error, "login_next": login_next},
    )


def save_paper_view(request):
    """Save a paper from search results. Redirects back to search."""
    if request.method != "POST":
        return redirect("search")

    if not request.user.is_authenticated:
        query = request.GET.get("q", "")
        next_url = reverse("search")
        if query:
            next_url += "?" + urlencode({"q": query})
        login_url = reverse("login") + "?" + urlencode({"next": next_url})
        return redirect(login_url)

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
        user=request.user,
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

    if not request.user.is_authenticated:
        return redirect("login")

    openalex_id = request.POST.get("openalex_id", "").strip()
    if openalex_id:
        SavedPaper.objects.filter(user=request.user, openalex_id=openalex_id).delete()

    return redirect("saved")


@login_required
def saved_view(request):
    """List all saved papers at /saved/."""
    papers = SavedPaper.objects.filter(user=request.user).order_by("-saved_at")
    return render(request, "papers/saved.html", {"papers": papers})


def register_view(request):
    """User registration."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "papers/register.html", {"form": form})


def login_view(request):
    """User login."""
    from django.contrib.auth.views import LoginView

    return LoginView.as_view(
        template_name="papers/login.html",
        redirect_authenticated_user=True,
    )(request)


def logout_view(request):
    """User logout."""
    from django.contrib.auth import logout

    logout(request)
    return redirect("home")
