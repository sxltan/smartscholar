# SmartScholar API Documentation

## 1. Overview

SmartScholar provides JSON API endpoints for searching academic papers, retrieving paper details, and accessing authenticated user data. The API supports programmatic access to search results from OpenAlex, individual paper metadata, and user-specific data such as saved papers, search history, and usage insights.

## 2. Base URL

During local development, the base URL is:

```
http://127.0.0.1:8000/
```

## 3. Authentication

**Public endpoints** (no authentication required):

- `GET /api/search/` – search papers
- `GET /api/paper/<openalex_id>/` – retrieve paper details

**Protected endpoints** (authentication required):

- `GET /api/saved-papers/` – list saved papers
- `GET /api/search-history/` – list search history
- `GET /api/insights/` – retrieve usage insights

Protected endpoints require the user to be logged in via Django session authentication. When an unauthenticated request is made to a protected endpoint, the API returns:

```json
{"error": "Authentication required"}
```

with HTTP status 401.

## 4. Endpoint Summary

| Method | Endpoint | Description | Authentication required |
|--------|----------|-------------|-------------------------|
| GET | `/api/search/` | Search papers and return JSON results | No |
| GET | `/api/paper/<openalex_id>/` | JSON details for a single paper | No |
| GET | `/api/saved-papers/` | List of user's saved papers | Yes |
| GET | `/api/search-history/` | List of user's search history | Yes |
| GET | `/api/insights/` | Statistics about saved papers and searches | Yes |

## 5. Detailed Endpoint Documentation

### Endpoint 1: GET /api/search/

**Purpose:** Search academic papers via the OpenAlex API and return results as JSON.

**HTTP method:** GET

**Route:** `/api/search/`

**Authentication:** Not required

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `sort` | string | No | Sort order; default `relevance` |
| `from_year` | string | No | Filter results from this year (inclusive) |
| `to_year` | string | No | Filter results up to this year (inclusive) |

**Valid `sort` values:**

- `relevance` – sort by relevance (default)
- `most_cited` – sort by citation count, descending
- `newest` – sort by publication year, descending

**Success response (200):** JSON object with `query`, `sort`, `from_year`, `to_year`, `count`, and `results` (array of paper objects). Each paper includes `title`, `publication_year`, `cited_by_count`, `first_author`, `openalex_id`, and `openalex_short_id`.

**Example request:**

```
GET /api/search/?q=machine+learning&sort=newest&from_year=2020&to_year=2024
```

**Example JSON response:**

```json
{
  "query": "machine learning",
  "sort": "newest",
  "from_year": "2020",
  "to_year": "2024",
  "count": 10,
  "results": [
    {
      "title": "Deep Learning for Natural Language Processing",
      "publication_year": 2024,
      "cited_by_count": 42,
      "first_author": "Jane Smith",
      "openalex_id": "https://openalex.org/W2101234567",
      "openalex_short_id": "W2101234567"
    }
  ]
}
```

**Error responses:**

| Status | Condition | Response |
|--------|-----------|----------|
| 400 | Missing query parameter | `{"error": "Query is required."}` |
| 400 | Invalid `from_year` or `to_year` (non-numeric) | `{"error": "Invalid from_year."}` or `{"error": "Invalid to_year."}` |
| 400 | `from_year` greater than `to_year` | `{"error": "from_year cannot be greater than to_year."}` |
| 503 | OpenAlex API unavailable | `{"error": "Unable to reach the search service."}` |

---

### Endpoint 2: GET /api/paper/<openalex_id>/

**Purpose:** Retrieve detailed information for a single paper by its OpenAlex ID.

**HTTP method:** GET

**Route:** `/api/paper/<openalex_id>/`

**Authentication:** Not required

**Path parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `openalex_id` | string | Yes | OpenAlex work ID (full URL or short ID, e.g. `W2101234567`) |

**Success response (200):** JSON object with paper details and related works. Fields include:

- `title` – paper title
- `publication_year` – year of publication
- `cited_by_count` – number of citations
- `authors` – array of author display names
- `openalex_id` – full OpenAlex URL
- `abstract` – reconstructed abstract text (or null)
- `related` – array of related paper objects (each with `title`, `publication_year`, `cited_by_count`, `first_author`, `openalex_id`, `openalex_short_id`)

**Example request:**

```
GET /api/paper/W2101234567/
```

**Example JSON response:**

```json
{
  "title": "Deep Learning for Natural Language Processing",
  "publication_year": 2024,
  "cited_by_count": 42,
  "authors": ["Jane Smith", "John Doe"],
  "openalex_id": "https://openalex.org/W2101234567",
  "abstract": "We present a novel approach to...",
  "related": [
    {
      "title": "Related Paper Title",
      "publication_year": 2023,
      "cited_by_count": 15,
      "first_author": "Alice Brown",
      "openalex_id": "https://openalex.org/W2100987654",
      "openalex_short_id": "W2100987654"
    }
  ]
}
```

**Error responses:**

| Status | Condition | Response |
|--------|-----------|----------|
| 400 | Missing or invalid paper ID | `{"error": "Paper ID is required."}` |
| 404 | Paper not found | `{"error": "<error message>"}` |
| 503 | Unable to retrieve paper details (OpenAlex unavailable or lookup failure) | `{"error": "Unable to load paper details. Please try again later."}` |

---

### Endpoint 3: GET /api/saved-papers/

**Purpose:** Return the current user's saved papers.

**HTTP method:** GET

**Route:** `/api/saved-papers/`

**Authentication:** Required

**Success response (200):** JSON array of saved paper objects, ordered by most recently saved first. Each object includes:

- `title` – paper title
- `openalex_id` – full OpenAlex URL
- `first_author` – first author name (or null)
- `publication_year` – year of publication (or null)
- `cited_by_count` – citation count
- `saved_at` – ISO 8601 timestamp when the paper was saved

**Example request:**

```
GET /api/saved-papers/
```

**Example JSON response:**

```json
[
  {
    "title": "Deep Learning for Natural Language Processing",
    "openalex_id": "https://openalex.org/W2101234567",
    "first_author": "Jane Smith",
    "publication_year": 2024,
    "cited_by_count": 42,
    "saved_at": "2024-03-10T14:30:00.000Z"
  }
]
```

**Error responses:**

| Status | Condition | Response |
|--------|-----------|----------|
| 401 | User not authenticated | `{"error": "Authentication required"}` |

---

### Endpoint 4: GET /api/search-history/

**Purpose:** Return the current user's search history, ordered by most recent first.

**HTTP method:** GET

**Route:** `/api/search-history/`

**Authentication:** Required

**Success response (200):** JSON array of search history entries. Each entry includes:

- `query` – the search query
- `searched_at` – ISO 8601 timestamp when the search was performed

**Example request:**

```
GET /api/search-history/
```

**Example JSON response:**

```json
[
  {
    "query": "machine learning",
    "searched_at": "2024-03-10T14:35:00.000Z"
  },
  {
    "query": "natural language processing",
    "searched_at": "2024-03-10T14:20:00.000Z"
  }
]
```

**Error responses:**

| Status | Condition | Response |
|--------|-----------|----------|
| 401 | User not authenticated | `{"error": "Authentication required"}` |

---

### Endpoint 5: GET /api/insights/

**Purpose:** Return aggregated statistics and insights about the user's saved papers and search activity.

**HTTP method:** GET

**Route:** `/api/insights/`

**Authentication:** Required

**Success response (200):** JSON object with the following fields:

- `saved_count` – total number of saved papers
- `search_count` – total number of searches performed
- `recent_searches` – array of up to 5 most recent searches (`query`, `searched_at`)
- `top_queries` – array of up to 5 most frequent search queries (`query`, `count`)
- `top_cited` – array of up to 5 most cited saved papers (`title`, `openalex_id`, `publication_year`, `cited_by_count`)
- `avg_citations` – average citation count across saved papers (or null if none)
- `newest_year` – most recent publication year among saved papers (or null)
- `oldest_year` – oldest publication year among saved papers (or null)

**Example request:**

```
GET /api/insights/
```

**Example JSON response:**

```json
{
  "saved_count": 12,
  "search_count": 45,
  "recent_searches": [
    {"query": "machine learning", "searched_at": "2024-03-10T14:35:00.000Z"}
  ],
  "top_queries": [
    {"query": "deep learning", "count": 8}
  ],
  "top_cited": [
    {
      "title": "Attention Is All You Need",
      "openalex_id": "https://openalex.org/W2102044381",
      "publication_year": 2017,
      "cited_by_count": 45000
    }
  ],
  "avg_citations": 1250.5,
  "newest_year": 2024,
  "oldest_year": 2015
}
```

**Error responses:**

| Status | Condition | Response |
|--------|-----------|----------|
| 401 | User not authenticated | `{"error": "Authentication required"}` |

## 6. Notes on Data Source

Paper search and paper detail data are retrieved from the OpenAlex API. Saved papers, search history, and insights are derived from the SmartScholar local database and user activity. The OpenAlex API provides publication metadata; the local database stores user-specific data such as saved papers and search history.

## 7. Error Handling Summary

| Status code | Meaning |
|-------------|---------|
| 200 | Success |
| 400 | Bad request (invalid or missing parameters) |
| 401 | Unauthorized (authentication required) |
| 404 | Not found |
| 503 | Service unavailable (external API unreachable) |
