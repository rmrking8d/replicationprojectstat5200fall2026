"""Reproduce Figure 5: participants' stated romance and mystery preferences."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from analysis_common import FIGURES_DIR, load_analysis_sample, save_table


def genre_preference_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate the share of participants assigning each rank to each genre."""
    rows = []
    for genre, column in (
        ("Romance", "romance_rank"),
        ("Mystery", "mystery_rank"),
    ):
        valid_ranks = data[column].dropna()
        if not valid_ranks.between(1, 5).all():
            raise ValueError(f"{genre} preference contains a rank outside 1-5")

        for rank in range(1, 6):
            rows.append(
                {
                    "genre": genre,
                    "rank": rank,
                    "share": valid_ranks.eq(rank).mean(),
                    "participants": int(len(valid_ranks)),
                }
            )

    return pd.DataFrame(rows)


def plot_figure5(summary: pd.DataFrame) -> None:
    """Save a grouped bar chart for romance and mystery preference ranks."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    romance = summary.loc[summary["genre"].eq("Romance")].set_index("rank")
    mystery = summary.loc[summary["genre"].eq("Mystery")].set_index("rank")
    ranks = range(1, 6)
    positions = list(ranks)
    width = 0.36

    fig, axis = plt.subplots(figsize=(7.4, 4.7))
    axis.bar(
        [rank - width / 2 for rank in positions],
        romance.loc[positions, "share"],
        width,
        color="#ff67a4",
        edgecolor="black",
        linewidth=0.5,
        label="Romance",
    )
    axis.bar(
        [rank + width / 2 for rank in positions],
        mystery.loc[positions, "share"],
        width,
        color="#777777",
        edgecolor="black",
        linewidth=0.5,
        label="Mystery",
    )
    axis.set_xticks(positions, ["1", "2", "3", "4", "5"])
    axis.set_xlabel("Stated taste for the genre (rank)")
    axis.set_ylabel("Percent of participants")
    axis.set_title("Stated preference over romance and mystery genres")
    axis.yaxis.set_major_formatter(
        matplotlib.ticker.PercentFormatter(xmax=1)
    )
    axis.legend(frameon=False, loc="upper right")
    axis.grid(axis="y", alpha=0.2)
    axis.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure5_genre_preferences.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "figure5_genre_preferences.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    data = load_analysis_sample()
    summary = genre_preference_summary(data)
    save_table(summary, "figure5_genre_preferences_summary")
    plot_figure5(summary)
    print(f"Saved Figure 5 outputs for {len(data):,} participants.")


if __name__ == "__main__":
    main()
