# Analysis code

The Python workflow is split into small scripts so each analysis and its
outputs stay easy to find. Run scripts from the project root; each script
resolves its input and output paths relative to its own location.

| Script | Purpose | Status |
|---|---|---|
| `00_prepare_data.py` | Verify raw-file checksums and archives; record input schemas and row counts. | Complete |
| `00_build_analysis_data.py` | Match Qualtrics participants to browsing data and build the analysis sample. | Implemented; sample-size difference under investigation |
| `01_table1_figure3_ad_effects.py` | Estimate ad effects on searches and purchases; create Table 1 and Figure 3. | Implemented; preliminary |
| `02_table2_figure4_genre_effects.py` | Estimate genre match-value effects; create Table 2 and Figure 4. | Implemented; preliminary |
| `03_table3_spillovers.py` | Estimate spillovers to similar nonadvertised books; create Table 3. | Implemented; preliminary |
| `04_figure5_genre_preferences.py` | Create Figure 5 from stated romance and mystery preferences. | Implemented; preliminary |

Original data under `data/raw/` are inputs only and are never modified by these
scripts. Processed data belong in `data/clean/`; generated tables and figures
belong in `results/tables/` and `results/figures/`, respectively.

The Python scripts use the authors' Stata and R replication code as a reference.
Generated estimates and graphs are preliminary until they have been checked
against the paper and the authors' processed data.

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
`results/data_build_report.json`. The remaining scripts save CSV and LaTeX
tables under `results/tables/` and PNG/PDF figures under `results/figures/`.

## Validation status

The current Python sample has 11,502 participants. The authors' processed
[`data_choices_for_R.csv`](https://github.com/ilyamorozov/adContent/blob/b9f5c0293fc516949e9e2d294caaab57885614c7/analysis/replication_package/temp/data_choices_for_R.csv)
at the pinned source revision has 11,498. Running the Python Table 1 estimator
on that author-processed file reproduces the authors' no-control Table 1 values
to the reported three decimals. The raw-to-clean build still differs by four
participants, and condition-specific search outcomes differ slightly. The
difference has not been resolved; observations have not been dropped simply
to force the reported sample size. Treat outputs generated from this project's
analysis sample as preliminary, not as an exact replication.
