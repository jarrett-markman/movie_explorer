import pandas as pd
import streamlit as st

from data import (
    get_api_key,
    search_movies,
    fetch_movie_by_id,
    fetch_movie_by_title,
)
from filters import (
    normalize_movie,
    format_revenue,
    format_votes,
    format_rating,
    format_runtime,
    format_metascore,
)
from charts import comparison_bar



# Page configuration
st.set_page_config(page_title="Movie Explorer", page_icon="🎬", layout="wide")
st.title("🎬 Movie Explorer")
st.caption("Powered by the OMDb API")

# Fail fast if the API key isn't configured.
if not get_api_key():
    st.error(
        "Missing OMDb API key. Add `OMDB_API_KEY = \"your_key\"` to "
        "`.streamlit/secrets.toml`, or set the `OMDB_API_KEY` environment variable. "
        "Get a free key at https://www.omdbapi.com/apikey.aspx."
    )
    st.stop()



# Mode selector
with st.sidebar:
    st.header("Navigation")
    mode = st.radio("Analysis Mode", ["Browse", "Compare"], key="mode")



#  BROWSE MODE — paginated title search + details viewer
if mode == "Browse":
    st.sidebar.header("Search")

    query_input = st.sidebar.text_input("Title contains", key="browse_query_input")
    year_input = st.sidebar.text_input("Year (optional)", key="browse_year", max_chars=4)
    type_input = st.sidebar.selectbox("Type", ["movie", "series", "episode"], key="browse_type")
    search_clicked = st.sidebar.button("🔎 Search", type="primary", use_container_width=True)

    # Persist the active search across reruns so pagination works.
    if "browse_active" not in st.session_state:
        st.session_state.browse_active = {"query": "", "year": "", "type": "movie", "page": 1}

    if search_clicked:
        st.session_state.browse_active = {
            "query": query_input.strip(),
            "year": year_input.strip(),
            "type": type_input,
            "page": 1,
        }

    active = st.session_state.browse_active

    if not active["query"] or len(active["query"]) < 2:
        st.info("Enter a title keyword in the sidebar and click **Search**.")
    else:
        with st.spinner(f"Searching for '{active['query']}'..."):
            result = search_movies(
                active["query"],
                year=active["year"],
                type_=active["type"],
                page=active["page"],
            )

        if result["error"]:
            st.warning(result["error"])
        elif not result["results"]:
            st.warning("No results.")
        else:
            total = result["total"]
            page = active["page"]
            total_pages = max(1, (total + 9) // 10)
            st.info(
                f"Page **{page}** of **{total_pages}** — **{total:,}** total results for "
                f"'{active['query']}'."
            )

            # Results table (lightweight — uses the 5 fields OMDb returns for searches).
            rows = []
            for r in result["results"]:
                poster = r.get("Poster")
                rows.append({
                    "Poster": poster if poster and poster != "N/A" else None,
                    "Title": r.get("Title", ""),
                    "Year": r.get("Year", ""),
                    "Type": r.get("Type", ""),
                    "IMDb ID": r.get("imdbID", ""),
                })
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
                column_config={"Poster": st.column_config.ImageColumn(width="small")},
            )

            # Pagination controls.
            prev_col, _, next_col = st.columns([1, 4, 1])
            with prev_col:
                if st.button("Previous", disabled=(page <= 1), use_container_width=True):
                    st.session_state.browse_active["page"] -= 1
                    st.rerun()
            with next_col:
                if st.button("Next", disabled=(page >= total_pages), use_container_width=True):
                    st.session_state.browse_active["page"] += 1
                    st.rerun()

            # Details viewer — pick one result to fetch full details on demand.
            st.divider()
            st.subheader("Movie Details")
            options = ["—"] + [
                f"{r['Title']} ({r['Year']}) — {r['IMDb ID']}" for r in rows
            ]
            pick = st.selectbox("Pick a movie on this page to see details", options, key="browse_pick")

            if pick != "—":
                imdb_id = pick.rsplit("—", 1)[-1].strip()
                with st.spinner("Fetching details..."):
                    raw = fetch_movie_by_id(imdb_id)

                if not raw:
                    st.error("Couldn't load details for that movie.")
                else:
                    m = normalize_movie(raw)
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if m["poster"]:
                            st.image(m["poster"], use_container_width=True)
                    with c2:
                        st.markdown(f"### {m['title']} ({m['year']})")
                        meta_bits = [b for b in [m["genre"], format_runtime(m["runtime"]), f"Rated {m['rated']}" if m["rated"] else ""] if b]
                        st.caption(" · ".join(meta_bits))

                        mc1, mc2, mc3, mc4 = st.columns(4)
                        mc1.metric("IMDb Rating", format_rating(m["rating"]))
                        mc2.metric("Votes", format_votes(m["votes"]))
                        mc3.metric("Box Office", format_revenue(m["revenue"]))
                        mc4.metric("Metascore", format_metascore(m["metascore"]))

                        if m["director"]:
                            st.markdown(f"**Director:** {m['director']}")
                        if m["actors"]:
                            st.markdown(f"**Cast:** {m['actors']}")
                        if m["plot"]:
                            st.markdown(f"**Plot:** {m['plot']}")
                        if m["awards"] and m["awards"] != "N/A":
                            st.markdown(f"**Awards:** {m['awards']}")


#  COMPARE MODE — two titles, side-by-side
elif mode == "Compare":
    st.sidebar.header("Compare Settings")

    title_a = st.sidebar.text_input("Movie A title", key="movie_a_title")
    year_a = st.sidebar.text_input("Year A (optional)", key="movie_a_year", max_chars=4)
    st.sidebar.divider()
    title_b = st.sidebar.text_input("Movie B title", key="movie_b_title")
    year_b = st.sidebar.text_input("Year B (optional)", key="movie_b_year", max_chars=4)

    st.sidebar.button("Compare", type="primary", use_container_width=True, key="compare_btn")

    st.subheader("Step 1 of 2: Pick Your Movies")
    if not title_a or not title_b:
        st.info("Enter both movie titles in the sidebar, then click **Compare**.")
    elif (
        title_a.strip().lower() == title_b.strip().lower()
        and year_a.strip() == year_b.strip()
    ):
        st.warning("Please pick two **different** movies to compare.")
    else:
        with st.spinner("Fetching both movies..."):
            raw_a = fetch_movie_by_title(title_a, year=year_a.strip())
            raw_b = fetch_movie_by_title(title_b, year=year_b.strip())

        missing = []
        if not raw_a:
            missing.append(f"'{title_a}'")
        if not raw_b:
            missing.append(f"'{title_b}'")

        if missing:
            st.error(
                f"Couldn't find: {', '.join(missing)}. Check the spelling, or try "
                "adding a year to disambiguate (e.g. there are multiple 'Dune' movies)."
            )
        else:
            movie_a = normalize_movie(raw_a)
            movie_b = normalize_movie(raw_b)

            st.subheader("Step 2 of 2: Comparison")
            st.toast("Comparison ready!")

            col1, col2 = st.columns(2)
            for col, m in [(col1, movie_a), (col2, movie_b)]:
                with col:
                    if m["poster"]:
                        st.image(m["poster"], width=220)
                    st.markdown(f"### 🎬 {m['title']} ({m['year']})")
                    if m["genre"]:
                        st.caption(m["genre"])
                    st.metric("IMDb Rating", format_rating(m["rating"]))
                    st.metric("Box Office", format_revenue(m["revenue"]))
                    st.metric("Runtime", format_runtime(m["runtime"]))
                    st.metric("Votes", format_votes(m["votes"]))
                    if m["director"]:
                        st.markdown(f"**Director:** {m['director']}")

            try:
                fig = comparison_bar(movie_a, movie_b)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Could not render comparison chart: {e}")
