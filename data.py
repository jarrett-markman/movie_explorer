import os

import requests
import streamlit as st

OMDB_BASE_URL = "https://www.omdbapi.com/"
REQUEST_TIMEOUT = 10  # seconds


def get_api_key():
    """Return the OMDb API key from Streamlit secrets or env var, or None."""
    try:
        if "OMDB_API_KEY" in st.secrets["api"]:
            return st.secrets["api"]["OMDB_API_KEY"]
    except Exception:
        # st.secrets raises if no secrets.toml exists; fall through to env var.
        pass
    return os.environ.get("OMDB_API_KEY")


def _require_api_key():
    """Return the API key, or halt the app with a helpful error."""
    key = get_api_key()
    if not key:
        st.error(
            "Missing OMDb API key. Add `OMDB_API_KEY = \"your_key\"` to "
            "`.streamlit/secrets.toml`, or set the `OMDB_API_KEY` environment variable. "
            "Get a free key at https://www.omdbapi.com/apikey.aspx"
        )
        st.stop()
    return key


@st.cache_data(ttl=3600, show_spinner=False)
def search_movies(
    query: str,
    year: str = "",
    type_: str = "movie",
    page: int = 1,
) -> dict:
    """
    Search OMDb by keyword (uses the `s=` endpoint). Cached for 1 hour.

    Returns a dict with:
      - results: list of {Title, Year, imdbID, Type, Poster}  (up to 10 per page)
      - total:   int, total results available across all pages
      - error:   str or None
    """
    if not query or len(query.strip()) < 2:
        return {"results": [], "total": 0, "error": "Please enter at least 2 characters."}

    params = {
        "apikey": _require_api_key(),
        "s": query.strip(),
        "page": page,
    }
    if year:
        params["y"] = year
    if type_:
        params["type"] = type_

    try:
        resp = requests.get(OMDB_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {"results": [], "total": 0, "error": f"Network error: {e}"}

    if data.get("Response") == "False":
        return {"results": [], "total": 0, "error": data.get("Error", "No results.")}

    return {
        "results": data.get("Search", []),
        "total": int(data.get("totalResults", 0)),
        "error": None,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_movie_by_id(imdb_id):
    """Fetch full movie details by IMDb ID (e.g. 'tt0111161'). Returns raw OMDb dict or None."""
    if not imdb_id:
        return None
    params = {"apikey": _require_api_key(), "i": imdb_id, "plot": "short"}
    try:
        resp = requests.get(OMDB_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None
    if data.get("Response") == "False":
        return None
    return data


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_movie_by_title(title, year = ""):
    """Fetch best-match movie details by title (uses the `t=` endpoint)."""
    if not title:
        return None
    params = {"apikey": _require_api_key(), "t": title.strip(), "plot": "short"}
    if year:
        params["y"] = year
    try:
        resp = requests.get(OMDB_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None
    if data.get("Response") == "False":
        return None
    return data
