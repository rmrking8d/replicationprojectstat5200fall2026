# Analysis code

The Python workflow is split into small scripts so each analysis and its
outputs stay easy to find. Run scripts from the project root; each script
resolves its input and output paths relative to its own location.

| Script | Purpose |
|---|---|
| `00_prepare_data.py` | Verify raw-file checksums and archives; record input schemas and row counts. |
| `00_build_analysis_data.py` | Match Qualtrics participants to browsing data and build the analysis sample. |
| `01_table1_figure3_ad_effects.py` | Estimate ad effects on searches and purchases; create Table 1 and Figure 3. |
| `02_table2_figure4_genre_effects.py` | Estimate genre match-value effects; create Table 2 and Figure 4. |
| `03_table3_spillovers.py` | Estimate spillovers to similar nonadvertised books; create Table 3. |
| `04_figure5_genre_preferences.py` | Create Figure 5 from stated romance and mystery preferences. |

Original data under `data/raw/` are inputs only and are never modified by these
scripts. Processed data belong in `data/clean/`; generated tables and figures
belong in `results/tables/` and `results/figures/`, respectively.

The Python scripts use the authors' Stata and R replication code as a reference.

## Run the workflow

From the project root, create a virtual environment and install the listed
dependencies:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

Then run the scripts in order:

```bash
./.venv/bin/python code/00_prepare_data.py
./.venv/bin/python code/00_build_analysis_data.py
./.venv/bin/python code/01_table1_figure3_ad_effects.py
./.venv/bin/python code/02_table2_figure4_genre_effects.py
./.venv/bin/python code/03_table3_spillovers.py
./.venv/bin/python code/04_figure5_genre_preferences.py
```

`00_prepare_data.py` creates `results/data_inventory.json` with raw-file
checksums, CSV row counts and columns, and ZIP validation results.
`00_build_analysis_data.py` creates `data/clean/analysis_sample.csv` and
`results/data_build_report.json`. The analysis scripts save CSV and LaTeX
tables under `results/tables/`, paper-style PDF and PNG versions of Tables 1–3
in the same folder, and PDF/PNG figures under `results/figures/`. Figure 3 is
also saved as separate Figure 3a search and Figure 3b purchase charts for direct
comparison with the authors' versions.
