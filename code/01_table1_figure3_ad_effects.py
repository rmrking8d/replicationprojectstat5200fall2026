"""Reproduce Table 1 and Figure 3: effects of advertising on searches/purchases."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats

from analysis_common import (
    CONDITION_NAMES,
    FIGURES_DIR,
    condition_sample,
    fit_robust_ols,
    load_analysis_sample,
    robust_linear_contrast,
    save_table,
)
from table_rendering import format_table_value, save_publication_table


BOOKS = {
    "Lost Girls": {
        "conditions": [0, 1, 2, 3],
        "search": "clicked_203",
        "purchase": "purchased_203",
    },
    "Stateline": {
        "conditions": [0, 4, 5, 6],
        "search": "clicked_303",
        "purchase": "purchased_303",
    },
}
TREATMENT_ROWS = [
    ("Plain ad", "ad_plain"),
    ("Genre ad", "ad_genre"),
    ("Price ad", "ad_price"),
]
CONTRAST_ROWS = [
    ("Genre - Plain", {"ad_genre": 1, "ad_plain": -1}),
    ("Price - Plain", {"ad_price": 1, "ad_plain": -1}),
    ("Price - Genre", {"ad_price": 1, "ad_genre": -1}),
]


def estimate_table1(data: pd.DataFrame) -> pd.DataFrame:
    """Estimate the unadjusted OLS treatment effects and planned contrasts."""
    rows: list[dict[str, object]] = []

    for book, specification in BOOKS.items():
        sample = condition_sample(data, specification["conditions"])
        sample["ad_plain"] = sample["ad_condition"].isin([2, 5]).astype(int)
        sample["ad_genre"] = sample["ad_condition"].isin([1, 4]).astype(int)
        sample["ad_price"] = sample["ad_condition"].isin([3, 6]).astype(int)
        regressors = sample[["ad_plain", "ad_genre", "ad_price"]]

        for outcome_label, outcome_column in (
            ("Search", specification["search"]),
            ("Purchase", specification["purchase"]),
        ):
            result = fit_robust_ols(sample, outcome_column, regressors)

            for treatment_label, coefficient in TREATMENT_ROWS:
                rows.append(
                    {
                        "book": book,
                        "outcome": outcome_label,
                        "effect": treatment_label,
                        "estimate": result.params[coefficient],
                        "standard_error": result.bse[coefficient],
                        "p_value": result.pvalues[coefficient],
                        "n": int(result.nobs),
                    }
                )

            for contrast_label, weights in CONTRAST_ROWS:
                estimate = robust_linear_contrast(result, weights)
                rows.append(
                    {
                        "book": book,
                        "outcome": outcome_label,
                        "effect": contrast_label,
                        **estimate,
                        "n": int(result.nobs),
                    }
                )

    return pd.DataFrame(rows)


def render_table1(table: pd.DataFrame) -> None:
    """Create a compact, paper-style version of Table 1."""
    rows: list[tuple[str, list[str]]] = []
    effects = [label for label, _ in TREATMENT_ROWS]
    contrasts = [label for label, _ in CONTRAST_ROWS]

    for panel, book in enumerate(BOOKS):
        panel_label = "A" if panel == 0 else "B"
        rows.append(
            (
                "panel",
                [f"Panel {panel_label}. {book}", "", "", "", "", "", ""],
            )
        )
        rows.append(
            (
                "heading",
                [f"ATE Regression Estimates ({book}):", "", "", "", "", "", ""],
            )
        )
        for effect in effects + contrasts:
            if effect == contrasts[0]:
                rows.append(
                    (
                        "subsection",
                        ["Implied ATE differences:", "", "", "", "", "", ""],
                    )
                )
            values = [effect]
            for outcome in ("Search", "Purchase"):
                estimate = table.loc[
                    table["book"].eq(book)
                    & table["outcome"].eq(outcome)
                    & table["effect"].eq(effect)
                ].iloc[0]
                values.extend(
                    format_table_value(
                        estimate[column],
                        p_value=column == "p_value",
                    )
                    for column in ("estimate", "standard_error", "p_value")
                )
            rows.append(("data", values))

    save_publication_table(
        "table1_ad_effects",
        "Table 1. Estimated advertising effects on searches and purchases",
        ["", "Est.", "S.E.", "P-value", "Est.", "S.E.", "P-value"],
        rows,
        [0.28, 0.12, 0.10, 0.14, 0.12, 0.10, 0.14],
        column_groups=[
            (1, 4, "Search"),
            (4, 7, "Purch."),
        ],
        note="OLS estimates with HC1 robust standard errors.",
    )


def _mean_confidence_interval(values: pd.Series) -> tuple[float, float, float]:
    """Return the sample mean and a two-sided 95% t confidence interval."""
    values = values.dropna().astype(float)
    mean = float(values.mean())
    if len(values) < 2:
        return mean, np.nan, np.nan
    standard_error = float(stats.sem(values))
    margin = float(stats.t.ppf(0.975, len(values) - 1) * standard_error)
    return mean, mean - margin, mean + margin


def figure3_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate the condition-specific means and confidence intervals."""
    rows: list[dict[str, object]] = []

    for book, specification in BOOKS.items():
        sample = condition_sample(data, specification["conditions"])
        for condition in specification["conditions"]:
            outcome_condition = sample.loc[sample["ad_condition"].eq(condition)]
            for outcome, outcome_column in (
                ("Search", specification["search"]),
                ("Purchase", specification["purchase"]),
            ):
                mean, lower, upper = _mean_confidence_interval(
                    outcome_condition[outcome_column]
                )
                rows.append(
                    {
                        "book": book,
                        "condition": condition,
                        "ad_type": CONDITION_NAMES[condition],
                        "outcome": outcome,
                        "mean": mean,
                        "ci_lower": lower,
                        "ci_upper": upper,
                        "n": len(outcome_condition),
                    }
                )

    return pd.DataFrame(rows)


def plot_figure3(summary: pd.DataFrame) -> None:
    """Save paper-sized Figure 3a/3b charts and a combined comparison copy."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    colors = {
        "No Ads": "#eff3ff",
        "Plain Ad": "#c6dbef",
        "Genre Ad": "#6baed6",
        "Price Ad": "#2171b5",
    }
    conditions = ["No Ads", "Plain Ad", "Genre Ad", "Price Ad"]
    books = list(BOOKS)
    x_positions = np.arange(len(books))
    width = 0.2

    def draw_panel(axis: plt.Axes, outcome: str) -> None:
        subset = summary.loc[summary["outcome"].eq(outcome)]
        for condition_index, condition in enumerate(conditions):
            condition_data = subset.loc[subset["ad_type"].eq(condition)].set_index("book")
            x = x_positions + (condition_index - 1.5) * width
            means = condition_data.loc[books, "mean"].to_numpy()
            lower = condition_data.loc[books, "ci_lower"].to_numpy()
            upper = condition_data.loc[books, "ci_upper"].to_numpy()
            axis.bar(
                x,
                means,
                width=width,
                color=colors[condition],
                edgecolor="black",
                linewidth=0.35,
                label=condition,
                zorder=3,
            )
            axis.errorbar(
                x,
                means,
                yerr=np.vstack([means - lower, upper - means]),
                fmt="none",
                ecolor="#222222",
                capsize=1.8,
                elinewidth=0.65,
                capthick=0.65,
                zorder=4,
            )

        axis.set_xticks(x_positions, books)
        axis.set_xlabel("Advertised book", labelpad=3)
        axis.set_ylabel(
            "Searched ad book" if outcome == "Search" else "Purchased ad book",
            labelpad=3,
        )
        axis.set_title(
            "Search rate of the advertised book"
            if outcome == "Search"
            else "Purchase rate of the advertised book",
            fontsize=10,
            pad=6,
        )
        axis.grid(axis="y", color="#e5e5e5", linewidth=0.55)
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(axis="both", labelsize=8, length=2.5, width=0.6)
        axis.spines["left"].set_linewidth(0.65)
        axis.spines["bottom"].set_linewidth(0.65)
        axis.set_xlim(-0.5, 1.5)

    for outcome, stem in (
        ("Search", "figure3a_searches"),
        ("Purchase", "figure3b_purchases"),
    ):
        figure, axis = plt.subplots(figsize=(5.2, 3.9))
        draw_panel(axis, outcome)
        axis.legend(
            frameon=False,
            ncol=4,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.22),
            fontsize=7.5,
            columnspacing=1.1,
            handlelength=1.2,
        )
        figure.subplots_adjust(left=0.14, right=0.98, top=0.88, bottom=0.25)
        figure.savefig(FIGURES_DIR / f"{stem}.png", dpi=300, facecolor="white")
        figure.savefig(FIGURES_DIR / f"{stem}.pdf", facecolor="white")
        plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(9.0, 3.9), sharey=False)
    for axis, outcome in zip(axes, ("Search", "Purchase"), strict=True):
        draw_panel(axis, outcome)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        frameon=False,
        ncol=4,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        fontsize=8,
    )
    figure.subplots_adjust(left=0.08, right=0.99, top=0.88, bottom=0.2, wspace=0.28)
    figure.savefig(FIGURES_DIR / "figure3_ad_effects.png", dpi=300, facecolor="white")
    figure.savefig(FIGURES_DIR / "figure3_ad_effects.pdf", facecolor="white")
    plt.close(figure)


def main() -> None:
    data = load_analysis_sample()
    table = estimate_table1(data)
    summary = figure3_summary(data)
    save_table(table, "table1_ad_effects")
    render_table1(table)
    save_table(summary, "figure3_ad_effects_summary")
    plot_figure3(summary)
    print(f"Saved Table 1 and Figure 3 outputs for {len(data):,} participants.")


if __name__ == "__main__":
    main()
