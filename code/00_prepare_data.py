"""Validate and inventory the raw data used by the replication.

This first preparation step deliberately does not alter or unpack the original
files. It checks each file against the SHA-256 checksum recorded at download
time, verifies ZIP archives, and records the schemas of available CSV files.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any, Iterable


# Resolve all project paths from this script so it can be run from any current
# working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = PROJECT_ROOT / "results" / "data_inventory.json"

# These checksums identify the exact raw files downloaded from the authors'
# repository. If a file changes, stop and investigate rather than silently
# treating the changed file as the original data.
EXPECTED_SHA256 = {
    "books_redeemed/redeemed_books.zip": (
        "727d0321b9638be0960d70713d04900089aea3f714cadd2b47300a9c548b06e6"
    ),
    "google_analytics/wave1/user_chronology.csv.zip": (
        "dedb1e300465ca63062e77fb0c13f23a9bf28afceb78fefcefed7ff506f70b50"
    ),
    "google_analytics/wave2/user_chronology.csv.zip": (
        "fe726d48171d8c67c50abe7d22281c08fb57b57dc6c2a699bd0d8dd335e748c2"
    ),
    "qualtrics/qualtrics_hashed.zip": (
        "d76f0e7a7eff2e09266b90d784eb44f4b65c56b346bbb76edc5275562fdd4ecd"
    ),
    "website_design/product_attr_pos.csv": (
        "298c51675de69102f43ca5c7bb727a6024be0ab6891fda475556f68341839af1"
    ),
    "website_design/product_sorting_full_store.csv": (
        "3b07167db484ac057d04ba3e81538f0589c342622bbf2c4154bd21a1c7a493ae"
    ),
    "woocommerce/order_exp_july5_aug3.csv": (
        "424cf1eeae9192f7a40063559e1a496c625fb799945ccb80e8a533eb56aff529"
    ),
    "woocommerce/order_exp_may19_july4.csv": (
        "91b8ed1589641cf9b0e03a5b19a53a6be4d4534ba6cf83857e6da74aa117655b"
    ),
}


def sha256_file(path: Path) -> str:
    """Return a file's SHA-256 digest without loading it all into memory."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        # Read in chunks so this also works efficiently for the large log files.
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def count_csv_rows(stream: Iterable[str]) -> tuple[list[str], int]:
    """Read a CSV header and count data rows, without retaining them in memory."""
    reader = csv.reader(stream)
    header = next(reader, [])
    row_count = sum(1 for _ in reader)
    return header, row_count


def inspect_csv(path: Path) -> dict[str, Any]:
    """Return a CSV's column names and data-row count."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        header, row_count = count_csv_rows(file)

    return {
        "columns": header,
        "rows": row_count,
    }


def inspect_zip(path: Path) -> dict[str, Any]:
    """Validate a ZIP archive and inspect any CSV members it contains."""
    csv_members: list[dict[str, Any]] = []

    with zipfile.ZipFile(path) as archive:
        # testzip returns the first corrupt member, or None when every member
        # passes its CRC check.
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ValueError(f"Corrupt ZIP member {corrupt_member!r} in {path}")

        # Ignore macOS resource-fork entries; they are not part of the dataset.
        data_members = [
            name
            for name in archive.namelist()
            if not name.startswith("__MACOSX/")
        ]
        csv_names = [
            name
            for name in data_members
            if name.lower().endswith(".csv")
        ]

        # Read CSVs directly from the archive so the raw directory remains
        # unchanged and no second, unpacked copy of large files is created.
        for name in csv_names:
            with archive.open(name) as binary_file:
                with io.TextIOWrapper(
                    binary_file,
                    encoding="utf-8-sig",
                    newline="",
                ) as text_file:
                    header, row_count = count_csv_rows(text_file)

            csv_members.append(
                {
                    "member": name,
                    "columns": header,
                    "rows": row_count,
                }
            )

        return {
            "zip_valid": True,
            "members": data_members,
            "csv_members": csv_members,
        }


def build_inventory() -> dict[str, Any]:
    """Validate every expected raw file and build a machine-readable inventory."""
    inventory: dict[str, Any] = {
        "source_repository": "https://github.com/ilyamorozov/adContent",
        "source_revision": "b9f5c0293fc516949e9e2d294caaab57885614c7",
        "files": [],
    }

    for relative_path, expected_digest in EXPECTED_SHA256.items():
        path = RAW_DATA_DIR / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Required raw data file is missing: {path}")

        actual_digest = sha256_file(path)
        if actual_digest != expected_digest:
            raise ValueError(
                f"Checksum mismatch for {path}: expected {expected_digest}, "
                f"found {actual_digest}"
            )

        file_record: dict[str, Any] = {
            "path": str(path.relative_to(PROJECT_ROOT)),
            "bytes": path.stat().st_size,
            "sha256": actual_digest,
        }

        if path.suffix.lower() == ".zip":
            file_record.update(inspect_zip(path))
        elif path.suffix.lower() == ".csv":
            file_record.update(inspect_csv(path))

        inventory["files"].append(file_record)

    return inventory


def main() -> None:
    """Write the validated inventory and report its location."""
    inventory = build_inventory()

    # Create output folders on demand; the repository may have no generated
    # results yet when this script is first run.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Validated {len(inventory['files'])} raw data files.")
    print(f"Data inventory written to {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
