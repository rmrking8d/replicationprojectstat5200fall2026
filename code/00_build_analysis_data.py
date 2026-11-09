"""Build the participant-level analysis file from the authors' raw inputs.

The script follows the sample construction and event definitions in the
authors' Stata replication scripts. It reads, but never changes, files in
``data/raw/``. Participant and browsing identifiers are used only in memory
for matching and are excluded from the saved analysis dataset.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DATA_DIR = PROJECT_ROOT / "data" / "clean"
REPORT_PATH = PROJECT_ROOT / "results" / "data_build_report.json"
ANALYSIS_DATA_PATH = CLEAN_DATA_DIR / "analysis_sample.csv"

# The target sample size is reported in Section 5.1 of the paper. We record a
# discrepancy for investigation rather than changing the sample silently.
PAPER_SAMPLE_SIZE = 11_498


def read_dta_from_zip(path: Path) -> pd.DataFrame:
    """Read the first Stata dataset in a ZIP archive without extracting it."""
    with zipfile.ZipFile(path) as archive:
        dta_files = [
            name for name in archive.namelist() if name.lower().endswith(".dta")
        ]
        if len(dta_files) != 1:
            raise ValueError(f"Expected one .dta file in {path}, found {dta_files}")

        data, _metadata = pyreadstat.read_dta(
            io.BytesIO(archive.read(dta_files[0])),
            apply_value_formats=False,
        )

    return data


def read_google_analytics() -> pd.DataFrame:
    """Combine the two raw Google Analytics event logs."""
    event_frames: list[pd.DataFrame] = []
    columns = [
        "client_id",
        "time",
        "category",
        "action",
        "label",
        "source_page",
    ]

    for wave in ("wave1", "wave2"):
        path = (
            RAW_DATA_DIR
            / "google_analytics"
            / wave
            / "user_chronology.csv.zip"
        )
        with zipfile.ZipFile(path) as archive:
            csv_files = [
                name
                for name in archive.namelist()
                if name.lower().endswith(".csv")
                and not name.startswith("__MACOSX/")
            ]
            if len(csv_files) != 1:
                raise ValueError(
                    f"Expected one chronology CSV in {path}, found {csv_files}"
                )
            with archive.open(csv_files[0]) as source:
                events = pd.read_csv(
                    source,
                    usecols=columns,
                    dtype="string",
                )

        event_frames.append(events)

    events = pd.concat(event_frames, ignore_index=True)

    # The authors convert Google Analytics timestamps from UTC to Chicago time.
    events["user_id"] = events["client_id"]
    events["time_stamp"] = pd.to_datetime(
        events["time"].str.slice(0, 19),
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    ) - pd.Timedelta(hours=5)

    if events["time_stamp"].isna().any():
        raise ValueError("Some Google Analytics timestamps could not be parsed")

    return events


def prepare_qualtrics() -> pd.DataFrame:
    """Apply the survey-side eligibility filters and prepare timestamps."""
    path = RAW_DATA_DIR / "qualtrics" / "qualtrics_hashed.zip"
    survey = read_dta_from_zip(path)

    # Match the authors' one-hour conversion from the survey time zone to
    # Chicago time. The raw survey records use mixed two- and four-digit years.
    for source, target in (("startdate", "start_time_cst"), ("enddate", "end_time_cst")):
        survey[target] = pd.to_datetime(
            survey[source],
            format="mixed",
            errors="coerce",
        ) + pd.Timedelta(hours=1)

    if survey[["start_time_cst", "end_time_cst"]].isna().any().any():
        raise ValueError("Some Qualtrics timestamps could not be parsed")

    # Remove test and preview responses, then keep people who passed either
    # comprehension check.
    survey = survey.loc[
        survey["hitid"].fillna("").ne("")
        & survey["distributionchannel"].ne("preview")
        & (survey["complottery"].eq(2) | survey["secondchancelottery"].eq(2))
    ].copy()

    survey["finished_survey"] = (
        survey["lostgirlsliking"].fillna("").ne("")
        & survey["statelineliking"].fillna("").ne("")
    )

    # A participant can have several attempts. Keep attempts up to and
    # including their first completed survey, and discard later attempts.
    survey = survey.sort_values(
        ["mturk_id", "start_time_cst", "responseid"],
        kind="stable",
    )
    survey["finished_survey_before"] = survey.groupby("mturk_id")[
        "finished_survey"
    ].transform(lambda completed: completed.shift(fill_value=False).cummax())
    survey = survey.loc[~survey["finished_survey_before"]].copy()

    survey["unique_code"] = survey["unique_code"].fillna("").str.upper()
    survey["book_code"] = survey["q66"].fillna("").astype("string").str.lower()

    # Stable row indices reproduce the authors' sequential matching order.
    survey = survey.reset_index(drop=True)
    survey["qualtrics_row"] = survey.index

    return survey


def match_survey_to_browsing(
    survey: pd.DataFrame,
    events: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Match survey attempts to browser IDs using coupon code and time window."""
    coupons = events.loc[
        events["category"].eq("Coupon"),
        ["user_id", "time", "time_stamp", "label"],
    ].copy()
    coupons["unique_code"] = coupons["label"].fillna("").str.upper()
    coupons = coupons.loc[
        coupons["unique_code"].str.len().isin([6, 7])
        & coupons["unique_code"].ne("TEST_C")
    ]

    # The authors match at most the first 25 uses of a code. Sort on the raw
    # timestamp text, as in their Stata script, before numbering those uses.
    coupons = coupons.sort_values(
        ["unique_code", "time"],
        kind="stable",
    )
    coupons["use_number"] = coupons.groupby("unique_code").cumcount() + 1
    coupons = coupons.loc[coupons["use_number"].le(25)]
    coupons = coupons.drop_duplicates(
        ["unique_code", "use_number", "user_id", "time_stamp"]
    )

    possible_matches = survey[
        [
            "qualtrics_row",
            "mturk_id",
            "unique_code",
            "start_time_cst",
            "end_time_cst",
        ]
    ].merge(
        coupons[["user_id", "unique_code", "time_stamp"]],
        on="unique_code",
        how="inner",
        validate="many_to_many",
    )
    possible_matches = possible_matches.loc[
        possible_matches["time_stamp"].between(
            possible_matches["start_time_cst"],
            possible_matches["end_time_cst"],
        )
    ].sort_values(
        ["qualtrics_row", "time_stamp"],
        kind="stable",
    )

    # A Google Analytics user can be assigned to only one survey attempt. For
    # each attempt, preserve the number of eligible candidate users and select
    # the earliest coupon use among users not already assigned.
    already_matched: set[str] = set()
    matches: list[dict[str, Any]] = []

    for qualtrics_row, candidates in possible_matches.groupby(
        "qualtrics_row",
        sort=True,
    ):
        candidates = candidates.loc[~candidates["user_id"].isin(already_matched)]
        candidates = candidates.drop_duplicates("user_id", keep="first")
        if candidates.empty:
            continue

        first_candidate = candidates.iloc[0]
        already_matched.add(str(first_candidate["user_id"]))
        matches.append(
            {
                "qualtrics_row": qualtrics_row,
                "user_id": first_candidate["user_id"],
                "candidate_count": len(candidates),
            }
        )

    matched_attempts = survey.merge(
        pd.DataFrame(matches, columns=["qualtrics_row", "user_id", "candidate_count"]),
        on="qualtrics_row",
        how="inner",
        validate="one_to_one",
    )

    # The source keeps the earliest matched attempt per MTurk participant.
    matched_attempts = matched_attempts.sort_values(
        ["mturk_id", "start_time_cst", "responseid"],
        kind="stable",
    ).drop_duplicates("mturk_id", keep="first")

    report = {
        "eligible_survey_attempts": int(len(survey)),
        "eligible_attempts_matched": int(len(matches)),
        "unique_survey_participants_matched": int(len(matched_attempts)),
        "ambiguous_matches": int(
            sum(match["candidate_count"] > 1 for match in matches)
        ),
    }

    return matched_attempts, report


def classify_events(events: pd.DataFrame) -> pd.DataFrame:
    """Apply the event classifications used in the authors' preparation code."""
    action = events["action"].fillna("")
    category = events["category"].fillna("")
    label = events["label"].fillna("")
    action_lower = action.str.lower()

    # These events are explicitly discarded by the authors before parsing.
    excluded = (
        action.isin(
            [
                "begin_checkout",
                "Started Checkout",
                "Completed Checkout",
                "Page Back",
                "Page Reload",
                "Tab ID",
            ]
        )
        | action_lower.isin(["remove_from_cart", "remove from cart"])
        | (category.eq("form") & action.eq("impression"))
        | category.isin(["ifso_tracking", "outbound-link"])
    )
    events = events.loc[~excluded].copy()

    action = events["action"].fillna("")
    category = events["category"].fillna("")
    label = events["label"].fillna("")
    action_lower = action.str.lower()
    event_type = pd.Series("", index=events.index, dtype="string")

    event_type.loc[category.eq("Coupon")] = "coupon_use"
    banner_view = action.eq("Viewed") & label.str.contains(
        "Banner|Tracker Bar",
        regex=True,
    )
    event_type.loc[banner_view] = "banner_view"
    banner_click = action.eq("Ad Banner Click") | (
        action.eq("Click") & label.str.contains("Banner", regex=False)
    )
    event_type.loc[banner_click] = "banner_click"
    event_type.loc[action_lower.isin(["add_to_cart", "add to cart"])] = "add_to_cart"
    event_type.loc[action_lower.isin(["checkout", "payment"])] = "checkout"
    event_type.loc[action.isin(["CLICK", "Page View - Custom"])] = "click"
    event_type.loc[action.eq("Saw Container")] = "visibility"

    unclassified = event_type.eq("")
    if unclassified.any():
        unexpected = (
            events.loc[unclassified, ["category", "action"]]
            .value_counts()
            .head(10)
            .to_dict()
        )
        raise ValueError(f"Unclassified browsing events remain: {unexpected}")

    events["event_type"] = event_type
    return events


def add_source_page_variables(
    events: pd.DataFrame,
    slug_to_item: dict[str, int],
) -> pd.DataFrame:
    """Derive list-page, genre, sorting, and product-page source variables."""
    source_page = events["source_page"].fillna("")
    source_lower = source_page.str.lower()

    events["source_genre"] = "default"
    genre_patterns = {
        "mystery": "product-category/mystery-thriller",
        "fantasy": "product-category/fantasy",
        "sci-fi": "product-category/science-fiction",
        "romance": "product-category/romance",
        "biography": "product-category/biography-memoir",
    }
    for genre, pattern in genre_patterns.items():
        events.loc[source_lower.str.contains(pattern, regex=False), "source_genre"] = genre

    events["source_sort"] = "default"
    is_price_desc = source_lower.str.contains("?orderby=price-desc", regex=False)
    is_price_asc = source_lower.str.contains("?orderby=price", regex=False)
    events.loc[is_price_desc, "source_sort"] = "price: desc"
    events.loc[is_price_asc & ~is_price_desc, "source_sort"] = "price: asc"
    events.loc[source_lower.str.contains("?s=", regex=False), "source_sort"] = "search query"

    events["source_type"] = "list"
    is_product_page = source_lower.str.contains("/product/", regex=False)
    events.loc[is_product_page, "source_type"] = "product_page"

    page_number = source_lower.str.extract(r"/page/(\d+)/", expand=False)
    events["source_npage"] = pd.to_numeric(page_number, errors="coerce").fillna(1).astype(int)

    slug = source_lower.str.extract(r"/product/([^/?]+)", expand=False)
    events["source_id"] = slug.map(slug_to_item)

    return events


def _condition_from_banner(label: str) -> int | None:
    """Map a banner/tracker-bar label to the source experiment condition."""
    if "whiteout" in label.lower() or "white" in label.lower():
        return 0
    for condition in range(1, 7):
        if str(condition) in label:
            return condition
    return None


def build_assignments(
    matched: pd.DataFrame,
    session_events: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Recover intended ad conditions and apply the authors' exclusions."""
    banner_events = session_events.loc[
        session_events["event_type"].eq("banner_view")
    ].copy()
    banner_events["banner_condition"] = banner_events["label"].fillna("").map(
        _condition_from_banner
    )
    if banner_events["banner_condition"].isna().any():
        raise ValueError("Some banner-view labels have no recognized condition")

    banner_events = banner_events.sort_values("time_stamp", kind="stable")
    exposure = banner_events.groupby("user_id").agg(
        exposure_condition=("banner_condition", "first"),
        number_of_conditions=("banner_condition", "nunique"),
    )

    coupon_events = session_events.loc[
        session_events["event_type"].eq("coupon_use")
    ].copy()
    coupon_events["coupon_code"] = coupon_events["label"].fillna("").str.upper()
    assigned_codes = coupon_events.loc[
        coupon_events["coupon_code"].str.len().eq(7)
        & coupon_events["coupon_code"].ne("TEST_C")
    ].sort_values(["user_id", "time"], kind="stable")
    assigned_codes = assigned_codes.drop_duplicates("user_id", keep="first")
    assigned_codes["code_condition"] = pd.to_numeric(
        assigned_codes["coupon_code"].str[0],
        errors="coerce",
    )

    assignments = matched.merge(
        exposure,
        left_on="user_id",
        right_index=True,
        how="left",
        validate="one_to_one",
    ).merge(
        assigned_codes[["user_id", "code_condition"]],
        on="user_id",
        how="left",
        validate="one_to_one",
    )
    assignments["assignment_mismatch"] = (
        assignments["code_condition"].notna()
        & assignments["exposure_condition"].notna()
        & assignments["code_condition"].ne(assignments["exposure_condition"])
    )
    assignments["ad_condition"] = assignments["code_condition"].fillna(
        assignments["exposure_condition"]
    )

    report = {
        "multiple_ad_exposure_participants": int(
            assignments["number_of_conditions"].gt(1).sum()
        ),
        "assignment_exposure_mismatches": int(
            assignments["assignment_mismatch"].sum()
        ),
        "missing_ad_condition": int(assignments["ad_condition"].isna().sum()),
    }

    # The source excludes multiple banner assignments and assignment/exposure
    # disagreements, then falls back to recorded exposure if no coupon code
    # encodes an intended assignment.
    assignments = assignments.loc[
        assignments["number_of_conditions"].fillna(0).le(1)
        & ~assignments["assignment_mismatch"]
        & assignments["ad_condition"].notna()
    ].copy()
    assignments["ad_condition"] = assignments["ad_condition"].astype(int)

    return assignments, report


def build_product_lookups() -> tuple[
    pd.DataFrame,
    dict[str, int],
    dict[str, int],
]:
    """Read book attributes and construct stable item-ID lookup dictionaries."""
    products = pd.read_csv(
        RAW_DATA_DIR / "website_design" / "product_sorting_full_store.csv"
    )
    products = products.rename(
        columns={
            "ID": "item_id",
            "Name": "full_name",
            "url_name": "short_name",
            "latest_price": "price",
            "position": "store_position",
            "Categories": "category",
        }
    )
    products["item_id"] = pd.to_numeric(products["item_id"], errors="raise").astype(int)
    products["price"] = pd.to_numeric(products["price"], errors="coerce")
    products["store_position"] = pd.to_numeric(
        products["store_position"],
        errors="raise",
    ).astype(int)
    products["store_page"] = 1 + ((products["store_position"] - 1) // 10)

    if products["item_id"].duplicated().any():
        raise ValueError("The authors' full-store product IDs are not unique")

    # Correct the four malformed URL slugs handled in the authors' Stata
    # item dictionary so product clicks and add-to-cart events map consistently.
    slug_corrections = {
        "don\u0092t-lie-to-me": "dont-lie-to-me",
        "almanack-naval-ravikant-wealth": "the-almanack-of-naval-ravikant",
        "ghost-secret-spymaster-james": "the-ghost",
        "hieronymous-bosch-a-mysterious-profile":
            "hieronymus-bosch-a-mysterious-profile",
    }
    products["short_name"] = products["short_name"].replace(slug_corrections)

    slug_to_item = dict(zip(products["short_name"], products["item_id"], strict=True))

    # Stata maps the Qualtrics book code using the product-attributes file.
    product_attributes = pd.read_csv(
        RAW_DATA_DIR / "website_design" / "product_attr_pos.csv",
        dtype={"SKU": "string"},
    )
    product_attributes["book_code"] = (
        product_attributes["SKU"].fillna("").str.lower()
    )
    product_attributes["item_id"] = pd.to_numeric(
        product_attributes["ID"],
        errors="raise",
    ).astype(int)
    book_code_to_item = dict(
        zip(
            product_attributes["book_code"],
            product_attributes["item_id"],
            strict=True,
        )
    )

    return products, slug_to_item, book_code_to_item


def parse_product_clicks(
    session_events: pd.DataFrame,
    products: pd.DataFrame,
    slug_to_item: dict[str, int],
) -> pd.DataFrame:
    """Translate the two different click-record formats into item IDs."""
    click_events = session_events.loc[
        session_events["event_type"].eq("click")
    ].copy()
    click_events["item_id"] = pd.Series(
        pd.NA,
        index=click_events.index,
        dtype="Int64",
    )

    # One event format stores the product URL in the label. The product slug
    # follows ``/product/`` and is mapped using the store's 100-book catalog.
    type_one = click_events["action"].eq("Page View - Custom") & click_events[
        "label"
    ].fillna("").str.contains("/product/", regex=False)
    click_events.loc[type_one, "item_id"] = (
        click_events.loc[type_one, "label"]
        .fillna("")
        .str.lower()
        .str.extract(r"/product/([^/?]+)", expand=False)
        .map(slug_to_item)
        .astype("Int64")
    )

    # The other event format stores the full product title rather than a URL.
    full_name_to_item = dict(
        zip(products["full_name"], products["item_id"], strict=True)
    )
    type_two = click_events["action"].eq("CLICK")
    click_events.loc[type_two, "item_id"] = (
        click_events.loc[type_two, "label"]
        .fillna("")
        .str.replace("&#8217;", "'", regex=False)
        .map(full_name_to_item)
        .astype("Int64")
    )

    # The authors retain only clicks that could be matched to a catalog item.
    click_events = click_events.loc[click_events["item_id"].notna()].copy()
    click_events["item_id"] = click_events["item_id"].astype(int)

    return click_events


def build_user_outcomes(
    assignments: pd.DataFrame,
    session_events: pd.DataFrame,
    survey_fields: pd.DataFrame,
    products: pd.DataFrame,
    book_code_to_item: dict[str, int],
    slug_to_item: dict[str, int],
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Construct the user-level outcomes required by Tables 1–3 and Figures 3–5."""
    clicks = parse_product_clicks(session_events, products, slug_to_item)
    clicks = add_source_page_variables(clicks, slug_to_item)
    products_by_id = products.set_index("item_id")
    clicks["price"] = clicks["item_id"].map(products_by_id["price"])
    clicks["category"] = clicks["item_id"].map(products_by_id["category"])

    # Translate product clicks into binary outcomes and spillover measures.
    clicks["clicked_203"] = clicks["item_id"].eq(203)
    clicks["clicked_303"] = clicks["item_id"].eq(303)
    clicks["clicked_cheap_other"] = (
        clicks["price"].le(1.00)
        & ~clicks["item_id"].isin([203, 303])
    )
    clicks["clicked_romance_other"] = (
        clicks["category"].eq("Romance") & clicks["item_id"].ne(203)
    )
    clicks["clicked_mystery_other"] = (
        clicks["category"].eq("Mystery/Thriller") & clicks["item_id"].ne(303)
    )

    # The authors count unique list-page/category/sort combinations from
    # visible product containers and product clicks as pages a participant
    # opened. Only these page-level fields are needed; individual visible
    # product IDs are not needed for the planned results.
    visibility_pages = session_events.loc[
        session_events["event_type"].eq("visibility")
    ].copy()
    visibility_pages = add_source_page_variables(visibility_pages, slug_to_item)
    visibility_pages = visibility_pages.loc[
        visibility_pages["label"].fillna("").str.contains("/product/", regex=False)
    ]
    page_columns = [
        "user_id",
        "source_npage",
        "source_type",
        "source_genre",
        "source_sort",
    ]
    pages = pd.concat(
        [
            visibility_pages[page_columns],
            clicks[page_columns],
        ],
        ignore_index=True,
    )
    pages = pages.loc[pages["source_type"].eq("list")].drop_duplicates()
    page_counts = pages.groupby("user_id").size().rename("pages_opened")

    search = clicks.groupby("user_id").agg(
        clicked_203=("clicked_203", "max"),
        clicked_303=("clicked_303", "max"),
        clicked_cheap_other=("clicked_cheap_other", "max"),
        clicked_romance_other=("clicked_romance_other", "max"),
        clicked_mystery_other=("clicked_mystery_other", "max"),
    )

    # Banner clicks are recorded both as explicit events and, in some sessions,
    # as a click on an ad-conditioned first-page product list.
    inferred_banner = (
        clicks["item_id"].isin([203, 303])
        & clicks["source_type"].eq("list")
        & clicks["source_genre"].ne("default")
        & clicks["source_sort"].ne("default")
        & clicks["source_npage"].eq(1)
    )
    inferred_banner_clicks = clicks.loc[inferred_banner].groupby("user_id").size().gt(0)
    tracked_banner_clicks = session_events.loc[
        session_events["event_type"].eq("banner_click")
    ].groupby("user_id").size().gt(0)
    banner_clicks = inferred_banner_clicks | tracked_banner_clicks

    # Add-to-cart events use the product slug in their source-page field.
    add_to_cart_events = session_events.loc[
        session_events["event_type"].eq("add_to_cart")
    ].copy()
    add_to_cart_events["item_id"] = (
        add_to_cart_events["source_page"]
        .fillna("")
        .str.lower()
        .str.extract(r"/product/([^/?]+)", expand=False)
        .map(slug_to_item)
    )
    # A small number of source-page URLs are malformed. The authors recover
    # those item IDs from another event with the same label.
    add_to_cart_events = add_to_cart_events.sort_values(
        ["label", "item_id"],
        kind="stable",
        na_position="last",
    )
    add_to_cart_events["item_id"] = add_to_cart_events.groupby(
        "label",
        dropna=False,
    )["item_id"].ffill()
    if add_to_cart_events["item_id"].isna().any():
        unmatched = (
            add_to_cart_events.loc[
                add_to_cart_events["item_id"].isna(),
                ["label", "source_page"],
            ]
            .drop_duplicates()
            .head(10)
            .to_dict("records")
        )
        raise ValueError(f"Unmatched add-to-cart events remain: {unmatched}")

    add_to_cart_events["added_to_cart203"] = add_to_cart_events["item_id"].eq(203)
    add_to_cart_events["added_to_cart303"] = add_to_cart_events["item_id"].eq(303)
    add_to_cart = add_to_cart_events.groupby("user_id").agg(
        added_to_cart203=("added_to_cart203", "max"),
        added_to_cart303=("added_to_cart303", "max"),
    )

    search = search.join(page_counts, how="outer")
    search = search.join(banner_clicks.rename("clicked_ad_banner"), how="outer")
    search = search.join(add_to_cart, how="outer")
    search["pages_opened"] = search["pages_opened"].fillna(1)
    search = search.fillna(False)

    # The authors use any visit to a genre filter or price sort as a user-level
    # spillover outcome. Apply the same source-page parsing to the session log.
    source_events = add_source_page_variables(
        session_events.copy(),
        slug_to_item,
    )
    sorting = source_events.assign(
        sorted_by_price_asc=lambda data: data["source_sort"].eq("price: asc"),
        sorted_by_price_desc=lambda data: data["source_sort"].eq("price: desc"),
        filtered_to_genre=lambda data: data["source_genre"].ne("default"),
        filtered_to_romance=lambda data: data["source_genre"].eq("romance"),
        filtered_to_thriller=lambda data: data["source_genre"].eq("mystery"),
    ).groupby("user_id")[
        [
            "sorted_by_price_asc",
            "sorted_by_price_desc",
            "filtered_to_genre",
            "filtered_to_romance",
            "filtered_to_thriller",
        ]
    ].max()

    # Recover the selected book from the returned survey response. The
    # authors' main analysis excludes participants without a mapped book code.
    purchase = assignments[["user_id", "book_code"]].copy()
    purchase["purchased_item_id"] = purchase["book_code"].map(book_code_to_item)
    valid_purchase = purchase["purchased_item_id"].notna()
    report = {
        "participants_with_ad_assignment": int(len(assignments)),
        "participants_with_mapped_book_code": int(valid_purchase.sum()),
        "participants_missing_or_unmapped_book_code": int((~valid_purchase).sum()),
        "participants_in_paper_analysis_sample": int(
            (valid_purchase & assignments["ad_condition"].notna()).sum()
        ),
    }
    purchase = purchase.loc[valid_purchase].copy()
    purchase["purchased_item_id"] = purchase["purchased_item_id"].astype(int)
    purchase["purchased_203"] = purchase["purchased_item_id"].eq(203)
    purchase["purchased_303"] = purchase["purchased_item_id"].eq(303)
    purchase["purchased_price"] = purchase["purchased_item_id"].map(
        products_by_id["price"]
    )
    purchase["purchased_category"] = purchase["purchased_item_id"].map(
        products_by_id["category"]
    )
    purchase["purchased_cheap_other"] = (
        purchase["purchased_price"].le(1.00)
        & ~purchase["purchased_item_id"].isin([203, 303])
    )
    purchase["purchased_romance_other"] = (
        purchase["purchased_category"].eq("Romance")
        & purchase["purchased_item_id"].ne(203)
    )
    purchase["purchased_mystery_other"] = (
        purchase["purchased_category"].eq("Mystery/Thriller")
        & purchase["purchased_item_id"].ne(303)
    )

    # Convert the survey's five-point attribute importance scales into the
    # numeric order used by the authors' tables.
    importance_scale = {
        "Not at all important": 1,
        "Slightly Important": 2,
        "Fairly Important": 3,
        "Important": 4,
        "Very Important": 5,
    }
    survey_variables = survey_fields.set_index("user_id")
    for column, source_column in (
        ("importance_price_num", "q561_1"),
        ("importance_genre_num", "q561_2"),
    ):
        survey_variables[column] = (
            survey_variables[source_column].map(importance_scale)
        )

    outcomes = (
        assignments.set_index("user_id")
        .join(search, how="left")
        .join(sorting, how="left")
        .join(
            purchase.drop(columns="book_code").set_index("user_id"),
            how="inner",
        )
        .join(
            survey_variables[
                [
                    "importance_price_num",
                    "importance_genre_num",
                ]
            ],
            how="left",
        )
    )

    # The source treats an ad-banner click, add-to-cart action, or purchase as
    # evidence that the corresponding advertised book was searched.
    lost_girls_ad = outcomes["ad_condition"].isin([1, 2, 3])
    stateline_ad = outcomes["ad_condition"].isin([4, 5, 6])
    outcomes.loc[
        outcomes["clicked_ad_banner"] & lost_girls_ad
        | outcomes["added_to_cart203"]
        | outcomes["purchased_203"],
        "clicked_203",
    ] = True
    outcomes.loc[
        outcomes["clicked_ad_banner"] & stateline_ad
        | outcomes["added_to_cart303"]
        | outcomes["purchased_303"],
        "clicked_303",
    ] = True

    # The rank variables use the original question order: fantasy, mystery,
    # romance, science fiction, and biography/memoir.
    outcomes = outcomes.rename(
        columns={
            "genrepreferences_1": "fantasy_rank",
            "genrepreferences_2": "mystery_rank",
            "genrepreferences_3": "romance_rank",
            "genrepreferences_4": "scifi_rank",
            "genrepreferences_5": "memoirs_rank",
        }
    )
    outcomes["ad_condition"] = outcomes["ad_condition"].astype(int)

    # Sort rows consistently, then remove all source identifiers. The finished
    # file contains only variables needed to reproduce the selected outputs.
    outcomes = outcomes.reset_index(drop=True)
    outcomes["analysis_row"] = range(1, len(outcomes) + 1)
    selected_columns = [
        "analysis_row",
        "ad_condition",
        "clicked_203",
        "clicked_303",
        "purchased_203",
        "purchased_303",
        "clicked_cheap_other",
        "clicked_ad_banner",
        "added_to_cart203",
        "added_to_cart303",
        "purchased_cheap_other",
        "clicked_romance_other",
        "clicked_mystery_other",
        "purchased_romance_other",
        "purchased_mystery_other",
        "sorted_by_price_asc",
        "sorted_by_price_desc",
        "filtered_to_genre",
        "filtered_to_romance",
        "filtered_to_thriller",
        "importance_price_num",
        "importance_genre_num",
        "romance_rank",
        "mystery_rank",
        "fantasy_rank",
        "scifi_rank",
        "memoirs_rank",
    ]
    outcomes = outcomes[selected_columns]

    boolean_columns = [
        "clicked_203",
        "clicked_303",
        "purchased_203",
        "purchased_303",
        "clicked_cheap_other",
        "clicked_ad_banner",
        "added_to_cart203",
        "added_to_cart303",
        "purchased_cheap_other",
        "clicked_romance_other",
        "clicked_mystery_other",
        "purchased_romance_other",
        "purchased_mystery_other",
        "sorted_by_price_asc",
        "sorted_by_price_desc",
        "filtered_to_genre",
        "filtered_to_romance",
        "filtered_to_thriller",
    ]
    outcomes[boolean_columns] = outcomes[boolean_columns].fillna(False).astype(int)

    return outcomes, report


def main() -> None:
    """Build the clean analysis file and write sample-construction diagnostics."""
    survey = prepare_qualtrics()
    events = read_google_analytics()
    matched, matching_report = match_survey_to_browsing(survey, events)

    # Restrict browsing events to each matched participant's survey window.
    session_events = events.merge(
        matched[["user_id", "start_time_cst", "end_time_cst"]],
        on="user_id",
        how="inner",
        validate="many_to_one",
    )
    session_events = session_events.loc[
        session_events["time_stamp"].between(
            session_events["start_time_cst"],
            session_events["end_time_cst"],
        )
    ].copy()
    session_events = classify_events(session_events)

    assignments, assignment_report = build_assignments(matched, session_events)
    products, slug_to_item, book_code_to_item = build_product_lookups()
    analysis_sample, outcome_report = build_user_outcomes(
        assignments,
        session_events,
        matched[["user_id", "q561_1", "q561_2"]].merge(
            matched[
                [
                    "user_id",
                    "genrepreferences_1",
                    "genrepreferences_2",
                    "genrepreferences_3",
                    "genrepreferences_4",
                    "genrepreferences_5",
                ]
            ],
            on="user_id",
            validate="one_to_one",
        ),
        products,
        book_code_to_item,
        slug_to_item,
    )

    # Main-analysis sample size can reveal a mistake in sample construction;
    # preserve the actual result and report any discrepancy clearly.
    sample_size = len(analysis_sample)
    report: dict[str, Any] = {
        "source_repository": "https://github.com/ilyamorozov/adContent",
        "source_revision": "b9f5c0293fc516949e9e2d294caaab57885614c7",
        "raw_survey_records": int(len(read_dta_from_zip(
            RAW_DATA_DIR / "qualtrics" / "qualtrics_hashed.zip"
        ))),
        "raw_google_analytics_events": int(len(events)),
        "events_in_matched_survey_windows": int(len(session_events)),
        **matching_report,
        **assignment_report,
        **outcome_report,
        "analysis_sample_size": int(sample_size),
        "paper_reported_sample_size": PAPER_SAMPLE_SIZE,
        "matches_paper_sample_size": sample_size == PAPER_SAMPLE_SIZE,
    }

    if sample_size != PAPER_SAMPLE_SIZE:
        report["sample_size_note"] = (
            "Sample differs from the paper; inspect matching, assignment, and "
            "purchase-code diagnostics before treating estimates as replicated."
        )

    CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    analysis_sample.to_csv(ANALYSIS_DATA_PATH, index=False)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Built analysis sample with {sample_size:,} participants.")
    print(f"Paper reports {PAPER_SAMPLE_SIZE:,} participants.")
    print(f"Analysis data: {ANALYSIS_DATA_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Build report: {REPORT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
