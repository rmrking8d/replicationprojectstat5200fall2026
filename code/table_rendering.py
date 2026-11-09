"""Render analysis tables as compact, paper-style PDF and PNG files."""

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
    """Save a lightly ruled table with the compact spacing of the paper tables."""
    if len(columns) != len(column_widths):
        raise ValueError("Each table column must have a corresponding width")
    if any(len(values) != len(columns) for _, values in rows):
        raise ValueError("Every table row must have one value per column")
    if any(kind not in {"panel", "heading", "section", "subsection", "data"} for kind, _ in rows):
        raise ValueError("Table rows must be sections, subsections, or data")
    if any(start >= end or start < 0 or end > len(columns) for start, end, _ in column_groups or []):
        raise ValueError("Column group bounds must match the table columns")

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    widths = np.asarray(column_widths, dtype=float)
    if (widths <= 0).any():
        raise ValueError("Column widths must be positive")
    x_edges = np.concatenate(([0.0], np.cumsum(widths / widths.sum())))

    row_units = [
        1.15 if kind in {"panel", "section"} else 1.05 if kind == "subsection" else 1.0
        for kind, _ in rows
    ]
    header_units = 1.7 if column_groups else 1.0
    note_units = 0.9 if note else 0.0
    vertical_units = 0.9 + header_units + sum(row_units) + note_units + 0.25
    figure_height = max(3.0, vertical_units * 0.24)
    figure, axis = plt.subplots(figsize=(7.5, figure_height))
    figure.subplots_adjust(left=0, right=1, bottom=0, top=1)
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    left, right = 0.035, 0.965
    x_positions = left + x_edges * (right - left)
    axis_height_inches = figure_height

    axis.text(
        left,
        1 - 0.12 / axis_height_inches,
        title,
        ha="left",
        va="top",
        fontsize=10,
        fontweight="bold",
        fontfamily="serif",
        transform=axis.transAxes,
    )

    y = 1 - 0.42 / axis_height_inches
    group_height = 0.23 / axis_height_inches if column_groups else 0.0
    if column_groups:
        for start, end, label in column_groups:
            axis.text(
                (x_positions[start] + x_positions[end]) / 2,
                y,
                label,
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                fontfamily="serif",
                transform=axis.transAxes,
            )
        y -= group_height

    header_height = 0.31 / axis_height_inches
    axis.plot(
        [left, right],
        [y + 0.17 / axis_height_inches] * 2,
        color="black",
        linewidth=0.55,
        transform=axis.transAxes,
        clip_on=False,
    )
    for index, label in enumerate(columns):
        is_label_column = index == 0
        x = (
            x_positions[index] + 0.006
            if is_label_column
            else x_positions[index + 1] - 0.006
        )
        axis.text(
            x,
            y - 0.04 / axis_height_inches,
            label,
            ha="left" if is_label_column else "right",
            va="center",
            fontsize=7.6,
            fontweight="bold",
            fontfamily="serif",
            transform=axis.transAxes,
        )
    y -= header_height
    axis.plot(
        [left, right],
        [y + 0.14 / axis_height_inches] * 2,
        color="black",
        linewidth=0.55,
        transform=axis.transAxes,
        clip_on=False,
    )

    for (kind, values), row_unit in zip(rows, row_units, strict=True):
        row_height = row_unit * 0.24 / axis_height_inches
        row_y = y - row_height / 2
        if kind in {"panel", "heading", "section", "subsection"}:
            axis.text(
                x_positions[0] + (0.006 if kind == "section" else 0.012),
                row_y,
                values[0],
                ha="left",
                va="center",
                fontsize=8 if kind in {"panel", "heading", "section"} else 7.7,
                fontweight="bold",
                fontstyle="italic" if kind in {"panel", "subsection"} else "normal",
                fontfamily="serif",
                transform=axis.transAxes,
            )
            if kind in {"panel", "section"}:
                axis.plot(
                    [left, right],
                    [y - 0.025 / axis_height_inches] * 2,
                    color="black",
                    linewidth=0.4,
                    transform=axis.transAxes,
                    clip_on=False,
                )
            if kind == "panel":
                axis.plot(
                    [left, right],
                    [y - row_height + 0.025 / axis_height_inches] * 2,
                    color="black",
                    linewidth=0.4,
                    transform=axis.transAxes,
                    clip_on=False,
                )
        else:
            for index, value in enumerate(values):
                is_label_column = index == 0
                x = (
                    x_positions[index] + 0.012
                    if is_label_column
                    else x_positions[index + 1] - 0.006
                )
                axis.text(
                    x,
                    row_y,
                    value,
                    ha="left" if is_label_column else "right",
                    va="center",
                    fontsize=7.5,
                    fontfamily="serif",
                    transform=axis.transAxes,
                )
        y -= row_height

    axis.plot(
        [left, right],
        [y] * 2,
        color="black",
        linewidth=0.55,
        transform=axis.transAxes,
        clip_on=False,
    )
    if note:
        axis.text(
            left,
            y - 0.12 / axis_height_inches,
            note,
            ha="left",
            va="top",
            fontsize=6.8,
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
