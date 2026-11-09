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

    fig, axis = plt.subplots(figsize=(6.0, 4.4))
    axis.bar(
        [rank - width / 2 for rank in positions],
        romance.loc[positions, "share"],
        width,
        color="#f65a9b",
        edgecolor="black",
        linewidth=0.45,
        label="Romance",
    )
    axis.bar(
        [rank + width / 2 for rank in positions],
        mystery.loc[positions, "share"],
        width,
        color="#4d4d4d",
        edgecolor="black",
        linewidth=0.45,
        label="Mystery",
    )
    axis.set_xticks(positions, ["1", "2", "3", "4", "5"])
    axis.set_xlabel("Stated taste for the genre (rank)", fontsize=9, labelpad=4)
    axis.set_ylabel("Share of participants", fontsize=9, labelpad=4)
    axis.set_title("Stated preference over romance and mystery genres", fontsize=10, pad=7)
    axis.set_ylim(0, 0.41)
    axis.set_yticks(
        [0, 0.1, 0.2, 0.3, 0.4],
        ["0", ".1", ".2", ".3", ".4"],
    )
    axis.legend(
        frameon=True,
        facecolor="white",
        edgecolor="#555555",
        fancybox=False,
        loc="upper center",
        ncol=2,
        fontsize=8,
        bbox_to_anchor=(0.5, 1.0),
        borderpad=0.35,
        handlelength=1.5,
    )
    axis.grid(axis="y", color="#e5e5e5", linewidth=0.55)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines["left"].set_linewidth(0.65)
    axis.spines["bottom"].set_linewidth(0.65)
    axis.tick_params(axis="both", labelsize=8, length=2.5, width=0.6)

    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.15, top=0.86)
    fig.savefig(FIGURES_DIR / "figure5_genre_preferences.png", dpi=300, facecolor="white")
    fig.savefig(FIGURES_DIR / "figure5_genre_preferences.pdf", facecolor="white")
    plt.close(fig)


def main() -> None:
    data = load_analysis_sample()
    summary = genre_preference_summary(data)
    save_table(summary, "figure5_genre_preferences_summary")
    plot_figure5(summary)
    print(f"Saved Figure 5 outputs for {len(data):,} participants.")


if __name__ == "__main__":
    main()
