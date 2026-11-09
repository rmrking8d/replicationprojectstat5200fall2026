"""Reproduce Table 2 and Figure 4: genre match value and preference effects."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_common import (
    FIGURES_DIR,
    condition_sample,
    fit_robust_ols,
    load_analysis_sample,
    save_table,
)
from table_rendering import format_table_value, save_publication_table


def _table_row(
    sample: pd.DataFrame,
    outcome: str,
    treatment: pd.Series,
    group_label: str,
    book: str,
    outcome_label: str,
) -> dict[str, object]:
    """Estimate a treatment effect within a preference subgroup."""
    analysis = sample.copy()
    analysis["treatment"] = treatment.loc[analysis.index].astype(int)
    regressors = analysis[["treatment"]]
    result = fit_robust_ols(analysis, outcome, regressors)
    return {
        "panel": book,
        "outcome": outcome_label,
        "preference_group": group_label,
        "plain_ad_mean": analysis.loc[analysis["treatment"].eq(0), outcome].mean(),
        "genre_ad_mean": analysis.loc[analysis["treatment"].eq(1), outcome].mean(),
        "estimate": result.params["treatment"],
        "standard_error": result.bse["treatment"],
        "p_value": result.pvalues["treatment"],
        "n": int(result.nobs),
    }


def estimate_table2(data: pd.DataFrame) -> pd.DataFrame:
    """Estimate genre-ad effects for each book and in the pooled sample."""
    rows: list[dict[str, object]] = []

    for book, conditions, rank_column, search_column, purchase_column in (
        ("Lost Girls", [1, 2], "romance_rank", "clicked_203", "purchased_203"),
        ("Stateline", [4, 5], "mystery_rank", "clicked_303", "purchased_303"),
    ):
        book_sample = condition_sample(data, conditions)
        book_sample["treatment"] = book_sample["ad_condition"].isin([1, 4]).astype(int)
        book_sample["preference_group"] = np.where(
            book_sample[rank_column].eq(1),
            "Ranked advertised genre 1st",
            "Ranked advertised genre 2nd-5th",
        )
        book_sample = book_sample.loc[book_sample[rank_column].between(1, 5)]

        for outcome_label, outcome_column in (
            ("Search", search_column),
            ("Purchase", purchase_column),
        ):
            for group_label in (
                "Ranked advertised genre 1st",
                "Ranked advertised genre 2nd-5th",
            ):
                subgroup = book_sample.loc[
                    book_sample["preference_group"].eq(group_label)
                ]
                rows.append(
                    _table_row(
                        subgroup,
                        outcome_column,
                        subgroup["treatment"],
                        group_label,
                        book,
                        outcome_label,
                    )
                )

    pooled = condition_sample(data, [1, 2, 4, 5])
    pooled["treatment"] = pooled["ad_condition"].isin([1, 4]).astype(int)
    pooled["advertised_genre_rank"] = pooled["romance_rank"].where(
        pooled["ad_condition"].isin([1, 2]),
        pooled["mystery_rank"],
    )
    pooled["clicked_ad_book"] = pooled["clicked_203"].where(
        pooled["ad_condition"].isin([1, 2]),
        pooled["clicked_303"],
    )
    pooled["purchased_ad_book"] = pooled["purchased_203"].where(
        pooled["ad_condition"].isin([1, 2]),
        pooled["purchased_303"],
    )
    pooled["preference_group"] = np.where(
        pooled["advertised_genre_rank"].eq(1),
        "Ranked advertised genre 1st",
        "Ranked advertised genre 2nd-5th",
    )
    pooled = pooled.loc[pooled["advertised_genre_rank"].between(1, 5)]

    for outcome_label, outcome_column in (
        ("Search", "clicked_ad_book"),
        ("Purchase", "purchased_ad_book"),
    ):
        for group_label in (
            "Ranked advertised genre 1st",
            "Ranked advertised genre 2nd-5th",
        ):
            subgroup = pooled.loc[pooled["preference_group"].eq(group_label)]
            rows.append(
                _table_row(
                    subgroup,
                    outcome_column,
                    subgroup["treatment"],
                    group_label,
                    "Pooled",
                    outcome_label,
                )
            )

    return pd.DataFrame(rows)


def render_table2(table: pd.DataFrame) -> None:
    """Create a paper-style table of genre-ad match-value estimates."""
    rows: list[tuple[str, list[str]]] = []
    panels = [
        ("Lost Girls", "Panel A. Advertising for Lost Girls", "Lost Girls", "romance"),
        ("Stateline", "Panel B. Advertising for Stateline", "Stateline", "mystery"),
        ("Pooled", "Panel C. Pooling Both Books", "advertised book", "ad genre"),
    ]
    preference_groups = [
        ("Ranked advertised genre 1st", "1st"),
        ("Ranked advertised genre 2nd-5th", "2nd-5th"),
    ]

    for panel, heading, book_name, genre in panels:
        rows.append(("panel", [heading, "", "", "", "", ""]))
        for outcome in ("Search", "Purchase"):
            measure = "search" if outcome == "Search" else "buy"
            rows.append(
                (
                    "subsection",
                    [f"Prob. {measure} {book_name}:", "", "", "", "", ""],
                )
            )
            for group, group_label in preference_groups:
                estimate = table.loc[
                    table["panel"].eq(panel)
                    & table["outcome"].eq(outcome)
                    & table["preference_group"].eq(group)
                ].iloc[0]
                rows.append(
                    (
                        "data",
                        [
                            f"Consumers who ranked {genre} {group_label}",
                            format_table_value(estimate["plain_ad_mean"]),
                            format_table_value(estimate["genre_ad_mean"]),
                            format_table_value(estimate["estimate"]),
                            format_table_value(estimate["standard_error"]),
                            format_table_value(estimate["p_value"], p_value=True),
                        ],
                    )
                )

    save_publication_table(
        "table2_genre_match_value",
        "Table 2. Match-value effects of genre advertising",
        ["", "Plain Ad", "Genre Ad", "Estimate", "S.E.", "p-value"],
        rows,
        [0.46, 0.11, 0.11, 0.12, 0.09, 0.11],
        note="OLS estimates with HC1 robust standard errors.",
    )


def _rank_specific_means(
    sample: pd.DataFrame,
    conditions: list[int],
    treatment_name: str,
) -> pd.DataFrame:
    """Compute the advertised-book search rate for each genre preference rank."""
    selected = sample.loc[
        sample["ad_condition"].isin(conditions)
    ].copy()
    lost_girls_conditions = [1, 2, 3]
    selected["advertised_genre_rank"] = selected["romance_rank"].where(
        selected["ad_condition"].isin(lost_girls_conditions),
        selected["mystery_rank"],
    )
    selected["search_rate"] = selected["clicked_203"].where(
        selected["ad_condition"].isin(lost_girls_conditions),
        selected["clicked_303"],
    )
    selected = selected.loc[selected["advertised_genre_rank"].between(1, 5)]
    return (
        selected.groupby("advertised_genre_rank", as_index=False)["search_rate"]
        .mean()
        .assign(ad_type=treatment_name)
    )


def figure4_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate Figure 4 search rates by ad type and preference rank."""
    rows = []
    for ad_content, conditions, treatment_conditions, treatment_label in (
        ("Genre", [1, 2, 4, 5], [1, 4], "Genre Ad"),
        ("Price", [2, 3, 5, 6], [3, 6], "Price Ad"),
    ):
        comparison = condition_sample(data, conditions)
        plain_conditions = [condition for condition in conditions if condition not in treatment_conditions]
        rows.extend(
            [
                _rank_specific_means(comparison, plain_conditions, "Plain Ad"),
                _rank_specific_means(comparison, treatment_conditions, treatment_label),
            ]
        )
        for row in rows[-2:]:
            row["ad_content"] = (
                "Plain vs Genre" if ad_content == "Genre" else "Plain vs Price"
            )

    return pd.concat(rows, ignore_index=True)


def plot_figure4(summary: pd.DataFrame) -> None:
    """Save the two-panel Figure 4 showing search rates across preference ranks."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.2), sharey=False)

    for axis, panel in zip(
        axes,
        ["Plain vs Genre", "Plain vs Price"],
        strict=True,
    ):
        subset = summary.loc[summary["ad_content"].eq(panel)]
        for ad_type, color, marker in (
            ("Plain Ad", "#315b8a", "o"),
            ("Genre Ad", "#a23b55", "s"),
            ("Price Ad", "#a23b55", "s"),
        ):
            plot_data = subset.loc[subset["ad_type"].eq(ad_type)].sort_values(
                "advertised_genre_rank"
            )
            if not plot_data.empty:
                axis.plot(
                    plot_data["advertised_genre_rank"],
                    plot_data["search_rate"],
                    marker=marker,
                    color=color,
                    linestyle="--" if ad_type != "Plain Ad" else "-",
                    linewidth=1.5,
                    markersize=5,
                    label=ad_type,
                )

        axis.set_xticks([1, 2, 3, 4, 5], ["1st", "2nd", "3rd", "4th", "5th"])
        axis.set_xlabel("Stated taste for the advertised genre (rank)", fontsize=9, labelpad=4)
        axis.set_ylabel("Search rate (advertised book)", fontsize=9, labelpad=4)
        axis.set_title(
            "(A) Genre Ads Polarize Search Probabilities"
            if panel == "Plain vs Genre"
            else "(B) Price Ads Increase Search Probabilities",
            fontsize=10,
            pad=7,
        )
        axis.grid(False)
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines["left"].set_linewidth(0.65)
        axis.spines["bottom"].set_linewidth(0.65)
        axis.tick_params(axis="both", labelsize=8, length=2.5, width=0.6)
        axis.legend(frameon=False, loc="upper right", fontsize=8)

    fig.subplots_adjust(left=0.08, right=0.99, bottom=0.18, top=0.88, wspace=0.30)
    fig.savefig(FIGURES_DIR / "figure4_preference_effects.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "figure4_preference_effects.pdf")
    plt.close(fig)


def main() -> None:
    data = load_analysis_sample()
    table = estimate_table2(data)
    summary = figure4_summary(data)
    save_table(table, "table2_genre_match_value")
    render_table2(table)
    save_table(summary, "figure4_preference_search_rates")
    plot_figure4(summary)
    print(f"Saved Table 2 and Figure 4 outputs for {len(data):,} participants.")


if __name__ == "__main__":
    main()
