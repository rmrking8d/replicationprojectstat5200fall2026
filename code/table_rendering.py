"""Render analysis tables as clean, paper-style PDF and PNG files."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from analysis_common import TABLES_DIR


def format_table_value(value: object, p_value: bool = False) -> str:
    """Format estimates consistently and avoid displaying tiny p-values as zero."""
    if value is None or not np.isfinite(float(value)):
        return ""
    number = float(value)
    if p_value and 0 <= number < 0.001:
        return "<0.001"
    if abs(number) < 0.0005:
        return "0.000"
    return f"{number:.3f}"


def save_publication_table(
    filename: str,
    title: str,
    columns: list[str],
    rows: list[tuple[str, list[str]]],
    column_widths: list[float],
    column_groups: list[tuple[int, int, str]] | None = None,
    note: str | None = None,
) -> None:
    """Save a lightly ruled, publication-style table as PDF and PNG."""
    if len(columns) != len(column_widths):
        raise ValueError("Each table column must have a corresponding width")
    if any(len(values) != len(columns) for _, values in rows):
        raise ValueError("Every table row must have one value per column")
    if any(kind not in {"section", "subsection", "data"} for kind, _ in rows):
        raise ValueError("Table rows must be sections, subsections, or data")

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    width_sum = sum(column_widths)
    normalized_widths = [width / width_sum for width in column_widths]
    x_edges = np.cumsum([0.0, *normalized_widths])

    row_inches = sum(
        0.34 if kind == "section" else 0.30 if kind == "subsection" else 0.29
        for kind, _ in rows
    )
    header_inches = 0.64 if column_groups else 0.39
    note_inches = 0.35 if note else 0.0
    content_inches = row_inches + header_inches + note_inches
    figure_height = max(2.6, 0.25 + content_inches / 0.78)
    figure, axis = plt.subplots(figsize=(12.0, figure_height))
    figure.subplots_adjust(left=0, right=1, bottom=0, top=1)
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    left = 0.025
    right = 0.975
    usable_width = right - left
    x_positions = left + x_edges * usable_width

    axis.text(
        left,
        0.975,
        title,
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        fontfamily="serif",
        transform=axis.transAxes,
    )

    axis_height_inches = figure_height
    y = 0.86
    if column_groups:
        group_height = 0.22 / axis_height_inches
        for start, end, label in column_groups:
            axis.text(
                (x_positions[start] + x_positions[end]) / 2,
                y,
                label,
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                fontfamily="serif",
                transform=axis.transAxes,
            )
        y -= group_height

    header_height = 0.35 / axis_height_inches
    axis.plot(
        [left, right],
        [y + header_height * 0.54] * 2,
        color="black",
        linewidth=0.8,
        transform=axis.transAxes,
        clip_on=False,
    )
    for column_index, label in enumerate(columns):
        is_label_column = column_index == 0
        x = (
            x_positions[column_index] + 0.006
            if is_label_column
            else x_positions[column_index + 1] - 0.006
        )
        axis.text(
            x,
            y,
            label,
            ha="left" if is_label_column else "right",
            va="center",
            fontsize=9,
            fontweight="bold",
            fontfamily="serif",
            transform=axis.transAxes,
        )
    y -= header_height
    axis.plot(
        [left, right],
        [y + header_height * 0.46] * 2,
        color="black",
        linewidth=0.8,
        transform=axis.transAxes,
        clip_on=False,
    )

    for kind, values in rows:
        row_inches = (
            0.34 if kind == "section" else 0.30 if kind == "subsection" else 0.29
        )
        row_height = row_inches / axis_height_inches
        row_y = y - row_height / 2
        if kind in {"section", "subsection"}:
            axis.text(
                x_positions[0] + 0.006,
                row_y,
                values[0],
                ha="left",
                va="center",
                fontsize=9.5 if kind == "section" else 9,
                fontweight="bold",
                fontfamily="serif",
                transform=axis.transAxes,
            )
            if kind == "section":
                axis.plot(
                    [left, right],
                    [y - row_height * 0.15] * 2,
                    color="black",
                    linewidth=0.45,
                    transform=axis.transAxes,
                    clip_on=False,
                )
        else:
            for column_index, value in enumerate(values):
                is_label_column = column_index == 0
                x = (
                    x_positions[column_index] + 0.006
                    if is_label_column
                    else x_positions[column_index + 1] - 0.006
                )
                axis.text(
                    x,
                    row_y,
                    value,
                    ha="left" if is_label_column else "right",
                    va="center",
                    fontsize=8.8,
                    fontfamily="serif",
                    transform=axis.transAxes,
                )
        y -= row_height

    axis.plot(
        [left, right],
        [y - 0.10 / axis_height_inches] * 2,
        color="black",
        linewidth=0.8,
        transform=axis.transAxes,
        clip_on=False,
    )
    if note:
        axis.text(
            left,
            max(0.015, y - 0.25 / axis_height_inches),
            note,
            ha="left",
            va="top",
            fontsize=8,
            fontfamily="serif",
            transform=axis.transAxes,
        )

    output_path = TABLES_DIR / filename
    figure.savefig(
        output_path.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    figure.savefig(
        output_path.with_suffix(".pdf"),
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)
