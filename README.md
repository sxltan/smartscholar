# SmartScholar

## Project Overview

SmartScholar is a Django web application that allows users to search academic papers using the OpenAlex API, an open scholarly database providing publication metadata. Users can view detailed information about papers, save papers to a personal library, and explore insights about their saved papers and search history. The application also exposes JSON API endpoints for programmatic access to search results, paper details, and user-specific data.

## Key Features

- Paper search using OpenAlex
- Sorting and filtering by publication year
- Paper detail pages with authors, citations, and related works
- Ability to save papers
- Personal search history tracking
- Insights dashboard for saved papers and searches
- JSON API endpoints for search, paper details, and user data

## Technology Stack

- Python
- Django
- SQLite (default Django database)
- OpenAlex API
- requests (for external API calls)
- HTML templates

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/sxltan/smartscholar.git
   cd smartscholar
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate
   ```
   On Windows: `venv\Scripts\activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Start the development server:
   ```
   python manage.py runserver
   ```

6. Open http://127.0.0.1:8000/ in your browser.

## Main Application Routes

- `/` – homepage
- `/search/` – search for papers
- `/paper/<openalex_id>/` – paper detail page
- `/saved/` – saved papers
- `/insights/` – user insights dashboard
- `/register/` – user registration
- `/login/` – user login
- `/logout/` – user logout

## JSON API Endpoints

- `/api/search/` – search papers and return JSON results
- `/api/paper/<openalex_id>/` – JSON details for a single paper
- `/api/saved-papers/` – JSON list of user's saved papers
- `/api/search-history/` – JSON list of user's search history
- `/api/insights/` – JSON statistics about saved papers and searches

Some endpoints require authentication.

## API Documentation

Detailed API documentation describing all endpoints, parameters, and response formats is provided as a PDF file in the repository:

`docs/api_documentation.pdf`

## Version Control

The project was developed using Git with a clear commit history to track development progress.

## License

This project was developed for academic coursework.
