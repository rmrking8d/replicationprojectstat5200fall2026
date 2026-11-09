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
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), sharey=False)

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
                    label=ad_type,
                )

        axis.set_xticks([1, 2, 3, 4, 5], ["1st", "2nd", "3rd", "4th", "5th"])
        axis.set_xlabel("Stated taste for the advertised genre (rank)")
        axis.set_ylabel("Search rate (advertised book)")
        axis.set_title(
            "(a) Genre ads polarize search probabilities"
            if panel == "Plain vs Genre"
            else "(b) Price ads increase search probabilities"
        )
        axis.grid(axis="y", alpha=0.2)
        axis.legend(frameon=False)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure4_preference_effects.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "figure4_preference_effects.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    data = load_analysis_sample()
    table = estimate_table2(data)
    summary = figure4_summary(data)
    save_table(table, "table2_genre_match_value")
    save_table(summary, "figure4_preference_search_rates")
    plot_figure4(summary)
    print(f"Saved Table 2 and Figure 4 outputs for {len(data):,} participants.")


if __name__ == "__main__":
    main()
