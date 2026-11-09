# Advertising Content and Consumer Search

Replication project for STAT 5200, Fall 2026.

## Research question

How does the information shown in an advertisement affect consumers' search and
purchasing decisions?

## Paper

Morozov, Ilya, and Anna Tuchman. “Where does advertising content lead you? We
created a bookstore to find out.” *Marketing Science* 43, no. 5 (2024):
986–1001.

The paper studies advertising content in a simulated online bookstore. In an
experiment, consumers see advertisements that reveal a low price, reveal a
book's genre, or provide no specific product information. The authors report
that revealing a low price consistently increases demand, genre information
has mixed effects, and advertising does not substantially increase total search.

## Replication scope

This project will replicate selected results from Section 5, “Experiment
Results”:

- Tables 1–3, covering estimated advertising effects on searches and purchases
  (Table 1), match-value effects of genre advertising (Table 2), and spillovers
  to similar nonadvertised books (Table 3).
- Figures 3–5 and their accompanying graphs.

The goal is to reproduce these results using the data and analysis materials
made available by the authors, then compare the reproduced results with those
reported in the paper.

## Data and materials

The authors' project repository is available at
[ilyamorozov/adContent](https://github.com/ilyamorozov/adContent). The raw
input files used for this replication have been downloaded into `data/raw/`
from a pinned revision of that repository. See
[`data/raw/README.md`](data/raw/README.md) for the source revision, file
inventory, and checksums. Raw data will be kept unchanged; processed data will
be saved separately.

## Project structure

- `code/` — scripts and other analysis code
- `data/raw/` — original, unmodified data
- `data/clean/` — cleaned and analysis-ready data
- `results/figures/` — replicated and generated figures
- `results/tables/` — replicated and generated tables (CSV, LaTeX, PDF, and PNG)

## Reproducibility

Instructions for building the analysis data and running the Python scripts are
in [`code/README.md`](code/README.md). The scripts are separated by analysis,
and generated tables and figures are saved in their corresponding `results/`
subfolders.
