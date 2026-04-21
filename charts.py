import pandas as pd
import plotly.express as px


def comparison_bar(movie_a, movie_b):
    """
    Grouped bar chart comparing two normalized movies across several metrics.
    Metrics with missing data on either side are silently skipped.
    """
    # (label, key_in_normalized_dict, transform_for_display)
    metric_specs = [
        ("Rating (0-10)",         "rating",    lambda x: x),
        ("Runtime (min)",         "runtime",   lambda x: x),
        ("IMDb Votes (thousands)","votes",     lambda x: x / 1000),
        ("Metascore (0-100)",     "metascore", lambda x: x),
    ]

    title_a = movie_a.get("title", "Movie A")
    title_b = movie_b.get("title", "Movie B")

    # Reshape into long form: one row per (metric, movie, value).
    rows = []
    for label, key, transform in metric_specs:
        av = movie_a.get(key)
        bv = movie_b.get(key)
        if av is None or bv is None:
            continue
        rows.append({"Metric": label, "Movie": title_a, "Value": transform(av)})
        rows.append({"Metric": label, "Movie": title_b, "Value": transform(bv)})

    compare_df = pd.DataFrame(rows, columns=["Metric", "Movie", "Value"])

    fig = px.bar(
        compare_df,
        x="Metric",
        y="Value",
        color="Movie",
        barmode="group",
        title="Side-by-Side Comparison",
        color_discrete_map={title_a: "#028090", title_b: "#E4572E"},
    )
    fig.update_layout(template="plotly_white", yaxis_title="Value")
    return fig