def _to_float(s):
    if s is None or s == "N/A":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _to_int(s):
    if s is None or s == "N/A":
        return None
    try:
        return int(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_runtime(s):
    """'148 min' -> 148"""
    if not s or s == "N/A":
        return None
    try:
        return int(str(s).split()[0])
    except (ValueError, IndexError):
        return None


def _parse_box_office(s):
    """'$123,456,789' -> 123456789. Often 'N/A' or missing entirely."""
    if not s or s == "N/A":
        return None
    try:
        return int(str(s).replace("$", "").replace(",", ""))
    except ValueError:
        return None



# Normalization
def normalize_movie(raw):
    """
    Convert a raw OMDb response into a typed, consistent dict.

    Raw OMDb fields we care about:
      Title, Year, Rated, Released, Runtime, Genre, Director, Actors,
      Plot, Poster, Metascore, imdbRating, imdbVotes, imdbID, BoxOffice.
    """
    if not raw:
        return {}

    poster = raw.get("Poster")
    if poster in (None, "", "N/A"):
        poster = None

    genre_str = raw.get("Genre", "") or ""
    genres = [g.strip() for g in genre_str.split(",") if g.strip()]

    return {
        "imdb_id": raw.get("imdbID", ""),
        "title": raw.get("Title", ""),
        "year": _to_int(raw.get("Year")),
        "rating": _to_float(raw.get("imdbRating")),
        "votes": _to_int(raw.get("imdbVotes")),
        "runtime": _parse_runtime(raw.get("Runtime")),
        "genre": genre_str,                 # original comma-separated string
        "genres": genres,                   # list form
        "director": raw.get("Director", ""),
        "actors": raw.get("Actors", ""),
        "plot": raw.get("Plot", ""),
        "poster": poster,
        "revenue": _parse_box_office(raw.get("BoxOffice")),
        "rated": raw.get("Rated", ""),
        "released": raw.get("Released", ""),
        "country": raw.get("Country", ""),
        "language": raw.get("Language", ""),
        "awards": raw.get("Awards", ""),
        "metascore": _to_int(raw.get("Metascore")),
    }



# Display formatters
def format_revenue(n):
    if n is None:
        return "N/A"
    if n >= 1_000_000_000:
        return f"${n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.1f}M"
    return f"${n:,}"


def format_votes(n):
    return "N/A" if n is None else f"{n:,}"


def format_rating(r):
    return "N/A" if r is None else f"{r:.1f}"


def format_runtime(m):
    return "N/A" if m is None else f"{m} min"


def format_metascore(m):
    return "N/A" if m is None else str(m)
