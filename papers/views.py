import requests
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Avg, Count, Max, Min
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.utils import timezone

from .models import SavedPaper, SearchHistory

OPENALEX_WORKS_URL = "https://api.openalex.org/works"

YEAR_CHOICES = [("", "Any")] + [(str(y), str(y)) for y in range(timezone.now().year, 1899, -1)]


def _openalex_short_id(url):
    """Extract short ID (e.g. W2101234009) from OpenAlex URL."""
    if not url:
        return ""
    return url.rstrip("/").split("/")[-1]


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

    openalex_id = work.get("id")
    result = {
        "title": work.get("title") or work.get("display_name") or "Unknown",
        "publication_year": work.get("publication_year"),
        "cited_by_count": work.get("cited_by_count", 0),
        "first_author": first_author,
        "openalex_id": openalex_id,
    }
    if openalex_id:
        result["openalex_short_id"] = _openalex_short_id(openalex_id)
    return result


def _extract_authors(work):
    """Extract list of author display names from an OpenAlex work."""
    authorships = work.get("authorships") or []
    names = []
    for a in authorships:
        author_obj = a.get("author")
        if author_obj:
            name = author_obj.get("display_name")
            if name:
                names.append(name)
    return names


def _reconstruct_abstract(abstract_inverted_index):
    """Reconstruct abstract text from OpenAlex inverted index format."""
    if not abstract_inverted_index:
        return None
    parts = []
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            parts.append((pos, word))
    parts.sort(key=lambda x: x[0])
    return " ".join(p[1] for p in parts)


def home_view(request):
    """Homepage at /."""
    return render(request, "papers/home.html")


def search_view(request):
    """Search papers at /search/ with optional sort and year filters."""
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "relevance").strip() or "relevance"
    from_year = request.GET.get("from_year", "").strip()
    to_year = request.GET.get("to_year", "").strip()
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

    def search_params():
        p = {"q": query, "sort": sort, "from_year": from_year, "to_year": to_year}
        return {k: v for k, v in p.items() if v}

    next_url = reverse("search")
    if search_params():
        next_url += "?" + urlencode(search_params())
    login_url = reverse("login") + "?" + urlencode({"next": next_url})

    if not query:
        return render(
            request,
            "papers/search.html",
            {
                "papers": [],
                "query": "",
                "sort": sort,
                "from_year": from_year,
                "to_year": to_year,
                "year_choices": YEAR_CHOICES,
                "saved_ids": saved_ids,
                "error": None,
                "login_url": login_url,
            },
        )

    from_year_int = None
    to_year_int = None
    if from_year:
        try:
            from_year_int = int(from_year)
        except ValueError:
            error = "Please enter a valid year for 'From year'."
    if to_year:
        try:
            to_year_int = int(to_year)
        except ValueError:
            error = "Please enter a valid year for 'To year'."
    if from_year_int is not None and to_year_int is not None and from_year_int > to_year_int:
        error = "'From year' cannot be greater than 'To year'."

    if error:
        return render(
            request,
            "papers/search.html",
            {
                "papers": [],
                "query": query,
                "sort": sort,
                "from_year": from_year,
                "to_year": to_year,
                "year_choices": YEAR_CHOICES,
                "saved_ids": saved_ids,
                "error": error,
                "login_url": login_url,
            },
        )

    api_params = {"search": query, "per_page": 10}
    if sort == "most_cited":
        api_params["sort"] = "cited_by_count:desc"
    elif sort == "newest":
        api_params["sort"] = "publication_year:desc"

    filters = []
    if from_year_int is not None:
        filters.append(f"from_publication_date:{from_year_int}-01-01")
    if to_year_int is not None:
        filters.append(f"to_publication_date:{to_year_int}-12-31")
    if filters:
        api_params["filter"] = ",".join(filters)

    try:
        response = requests.get(OPENALEX_WORKS_URL, params=api_params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return render(
            request,
            "papers/search.html",
            {
                "papers": [],
                "query": query,
                "sort": sort,
                "from_year": from_year,
                "to_year": to_year,
                "year_choices": YEAR_CHOICES,
                "saved_ids": saved_ids,
                "error": "Unable to reach the search service. Please try again later.",
                "login_url": login_url,
            },
        )

    results = data.get("results") or []
    papers = [_extract_paper(w) for w in results]

    if request.user.is_authenticated:
        SearchHistory.objects.create(user=request.user, query=query)

    save_params = {"q": query}
    if sort:
        save_params["sort"] = sort
    if from_year:
        save_params["from_year"] = from_year
    if to_year:
        save_params["to_year"] = to_year
    save_redirect_params = urlencode(save_params)

    return render(
        request,
        "papers/search.html",
        {
            "papers": papers,
            "query": query,
            "sort": sort,
            "from_year": from_year,
            "to_year": to_year,
            "year_choices": YEAR_CHOICES,
            "saved_ids": saved_ids,
            "error": error,
            "login_url": login_url,
            "save_redirect_params": save_redirect_params,
        },
    )


def paper_detail_view(request, openalex_id):
    """Paper detail page with related papers."""
    if not openalex_id:
        return redirect("search")

    if openalex_id.startswith("http"):
        short_id = _openalex_short_id(openalex_id)
        work_url = f"https://api.openalex.org/works/{short_id}"
    else:
        work_url = f"https://api.openalex.org/works/{openalex_id}"

    try:
        response = requests.get(work_url, timeout=10)
        response.raise_for_status()
        work = response.json()
    except requests.RequestException:
        return render(
            request,
            "papers/paper_detail.html",
            {"error": "Unable to load paper details. Please try again later."},
        )

    openalex_id_full = work.get("id")
    title = work.get("title") or work.get("display_name") or "Unknown"
    publication_year = work.get("publication_year")
    cited_by_count = work.get("cited_by_count", 0)
    authors = _extract_authors(work)
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

    related = []
    ref_urls = work.get("referenced_works") or work.get("related_works") or []
    for ref_url in ref_urls[:5]:
        try:
            ref_id = _openalex_short_id(ref_url)
            ref_api_url = f"https://api.openalex.org/works/{ref_id}"
            ref_response = requests.get(ref_api_url, timeout=5)
            ref_response.raise_for_status()
            ref_work = ref_response.json()
            related.append(_extract_paper(ref_work))
        except requests.RequestException:
            continue

    is_saved = False
    if request.user.is_authenticated and openalex_id_full:
        is_saved = SavedPaper.objects.filter(
            user=request.user, openalex_id=openalex_id_full
        ).exists()

    short_id = _openalex_short_id(openalex_id_full) if openalex_id_full else ""
    paper_detail_url = reverse("paper_detail", kwargs={"openalex_id": short_id})
    save_redirect_params = urlencode({"next": paper_detail_url})
    login_url = reverse("login") + "?" + urlencode({"next": request.path})
    unsave_redirect_params = urlencode({"next": paper_detail_url})

    return render(
        request,
        "papers/paper_detail.html",
        {
            "paper": {
                "title": title,
                "publication_year": publication_year,
                "cited_by_count": cited_by_count,
                "authors": authors,
                "openalex_id": openalex_id_full,
                "abstract": abstract,
            },
            "related": related,
            "is_saved": is_saved,
            "save_redirect_params": save_redirect_params,
            "login_url": login_url,
            "unsave_redirect_params": unsave_redirect_params,
        },
    )


def save_paper_view(request):
    """Save a paper from search results or detail page. Redirects back appropriately."""
    if request.method != "POST":
        return redirect("search")

    if not request.user.is_authenticated:
        next_param = request.GET.get("next", "")
        if next_param and next_param.startswith("/"):
            next_url = next_param
        else:
            params = {k: v for k, v in request.GET.items() if k != "next" and v}
            next_url = reverse("search") + ("?" + urlencode(params) if params else "")
        login_url = reverse("login") + "?" + urlencode({"next": next_url})
        return redirect(login_url)

    openalex_id = request.POST.get("openalex_id", "").strip()
    if not openalex_id:
        return redirect("search")

    next_param = request.GET.get("next", "")
    if next_param and next_param.startswith("/"):
        redirect_url = next_param
    else:
        query = request.GET.get("q", "")
        sort = request.GET.get("sort", "")
        from_year = request.GET.get("from_year", "")
        to_year = request.GET.get("to_year", "")
        params = {}
        if query:
            params["q"] = query
        if sort:
            params["sort"] = sort
        if from_year:
            params["from_year"] = from_year
        if to_year:
            params["to_year"] = to_year
        redirect_url = reverse("search")
        if params:
            redirect_url += "?" + urlencode(params)

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
    """Remove a saved paper. Redirects to next param if safe, otherwise to saved page."""
    if request.method != "POST":
        return redirect("saved")

    if not request.user.is_authenticated:
        return redirect("login")

    openalex_id = request.POST.get("openalex_id", "").strip()
    if openalex_id:
        SavedPaper.objects.filter(user=request.user, openalex_id=openalex_id).delete()

    next_param = request.GET.get("next", "").strip()
    if next_param and next_param.startswith("/") and not next_param.startswith("//"):
        return redirect(next_param)
    return redirect("saved")


@login_required
def saved_view(request):
    """List all saved papers at /saved/."""
    papers = list(SavedPaper.objects.filter(user=request.user).order_by("-saved_at"))
    for p in papers:
        p.openalex_short_id = _openalex_short_id(p.openalex_id)
    return render(request, "papers/saved.html", {"papers": papers})


@login_required
def insights_view(request):
    """Search insights dashboard for the current user."""
    user_saved = SavedPaper.objects.filter(user=request.user)
    user_searches = SearchHistory.objects.filter(user=request.user)

    saved_count = user_saved.count()
    search_count = user_searches.count()
    recent_searches = user_searches.order_by("-searched_at")[:5]

    top_queries = (
        user_searches.values("query")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    top_cited = user_saved.order_by("-cited_by_count")[:5]

    stats = user_saved.aggregate(
        avg_citations=Avg("cited_by_count"),
        newest_year=Max("publication_year"),
        oldest_year=Min("publication_year"),
    )

    return render(
        request,
        "papers/insights.html",
        {
            "saved_count": saved_count,
            "search_count": search_count,
            "recent_searches": recent_searches,
            "top_queries": top_queries,
            "top_cited": top_cited,
            "avg_citations": stats["avg_citations"],
            "newest_year": stats["newest_year"],
            "oldest_year": stats["oldest_year"],
        },
    )


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
