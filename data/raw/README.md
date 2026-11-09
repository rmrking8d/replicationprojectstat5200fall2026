# Raw data provenance

These are the original input files used in the authors' replication package.
They were downloaded without modification from
[ilyamorozov/adContent](https://github.com/ilyamorozov/adContent), revision
[`b9f5c0293fc516949e9e2d294caaab57885614c7`](https://github.com/ilyamorozov/adContent/tree/b9f5c0293fc516949e9e2d294caaab57885614c7),
on November 9, 2026.

The authors' README says the Qualtrics data have had IP addresses removed and
MTurk IDs hashed. It also asks researchers using the data to cite the paper:

> Morozov, Ilya, and Anna Tuchman. “Where Does Advertising Content Lead You?
> We Created a Bookstore to Find Out.” *Marketing Science* 43, no. 5 (2024):
> 986–1001.

## Files

| File | Contents |
|---|---|
| `books_redeemed/redeemed_books.zip` | Unredeemed books data (`.dta` archive) |
| `google_analytics/wave1/user_chronology.csv.zip` | Wave 1 Google Analytics event chronology |
| `google_analytics/wave2/user_chronology.csv.zip` | Wave 2 Google Analytics event chronology |
| `qualtrics/qualtrics_hashed.zip` | Hashed Qualtrics survey data (`.dta` archive) |
| `website_design/product_attr_pos.csv` | Product attributes and positions |
| `website_design/product_sorting_full_store.csv` | Product sorting in the full store |
| `woocommerce/order_exp_may19_july4.csv` | WooCommerce orders, May 19–July 4 |
| `woocommerce/order_exp_july5_aug3.csv` | WooCommerce orders, July 5–August 3 |

The authors note that their Comscore data, used for an appendix figure, are not
included in the public repository. They are not needed for this project's
planned replication of Figures 3–5.

## SHA-256 checksums

| File | SHA-256 |
|---|---|
| `books_redeemed/redeemed_books.zip` | `727d0321b9638be0960d70713d04900089aea3f714cadd2b47300a9c548b06e6` |
| `google_analytics/wave1/user_chronology.csv.zip` | `dedb1e300465ca63062e77fb0c13f23a9bf28afceb78fefcefed7ff506f70b50` |
| `google_analytics/wave2/user_chronology.csv.zip` | `fe726d48171d8c67c50abe7d22281c08fb57b57dc6c2a699bd0d8dd335e748c2` |
| `qualtrics/qualtrics_hashed.zip` | `d76f0e7a7eff2e09266b90d784eb44f4b65c56b346bbb76edc5275562fdd4ecd` |
| `website_design/product_attr_pos.csv` | `298c51675de69102f43ca5c7bb727a6024be0ab6891fda475556f68341839af1` |
| `website_design/product_sorting_full_store.csv` | `3b07167db484ac057d04ba3e81538f0589c342622bbf2c4154bd21a1c7a493ae` |
| `woocommerce/order_exp_july5_aug3.csv` | `424cf1eeae9192f7a40063559e1a496c625fb799945ccb80e8a533eb56aff529` |
| `woocommerce/order_exp_may19_july4.csv` | `91b8ed1589641cf9b0e03a5b19a53a6be4d4534ba6cf83857e6da74aa117655b` |

The source repository also contains Stata and R replication scripts. Those will
be used as references while implementing the analysis in Python; they have not
been run or translated yet.
