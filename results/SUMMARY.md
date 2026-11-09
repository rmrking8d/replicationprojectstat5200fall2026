# Replication Summary

*Seven-minute presentation outline*

## 1. Introduction and motivation *(about 2.5 minutes)*

- **Economic question:** Which product attributes should a firm reveal in an
  ad? Does revealing price or genre increase demand for the advertised book,
  and does the effect of genre information vary with consumers' tastes?
- **Why it matters:** Firms spend heavily on advertising, but the creative
  itself—not just whether an ad was shown—may help explain why advertising
  succeeds or fails. The authors note that practitioners offer competing
  advice: emphasize what makes a product unique, or emphasize attributes that
  matter most to the target buyer.
- **Five literature streams in the paper:**
  1. **What advertising says and whether content matters.** Early content
     audits document how much factual information appears in TV ads (Resnik
     and Stern, 1977; Stern and Resnik, 1991; Abernethy and Franke, 1996), but
     do not test how content changes consumer choices. Later observational
     studies associate creative features with engagement, search, or sales:
     for example, Liaukonyte, Teixeira, and Wilbur (2015) relate TV-ad focus
     (action, information, emotion, imagery) to online shopping, while Du,
     Xu, and Wilbur (2019) find stronger search responses to informative and
     likable creatives. These relationships can be confounded because firms
     choose which ads to show to which audiences and when. Quasi-experimental
     work (Lee, Hosanagar, and Nair, 2018; Tsai and Honka, 2021) advances
     identification but, as the paper notes, still calls for experiments.
  2. **Experiments that manipulate ad content.** The paper identifies a
     smaller experimental literature. Lodish et al. (1995) synthesize split-
     cable TV copy tests and find stronger effects when copy introduces
     attributes; Bertrand et al. (2010) randomize consumer-credit ad content;
     and Biswas (2020) studies discount information in food-delivery ads.
     These studies establish that content can matter, but provide limited
     evidence on how revealing product attributes changes consumers'
     *search process* and choices across people with different tastes.
  3. **Advertising and consumer search.** Prior work estimates advertising's
     relationship with awareness, search, and choice, often using
     observational data (e.g., Honka, Hortacsu, and Vitorino, 2017; Tsai and
     Honka, 2021; Ursu, Simonov, and An, 2021). Fong (2017) uses a field
     experiment on targeted marketing emails to identify effects on website
     search, but the treatment is ad exposure/targeting rather than the
     attribute content of an ad. Morozov and Tuchman bridge these questions by
     randomizing both whether an ad appears and which information it reveals,
     while tracking browsing.
  4. **Theory of information, persuasion, and search.** Nelson (1974) and
     Milgrom and Roberts (1986) provide foundations for advertising as
     information or as a signal of product quality. Search/prominence models
     (Arbatskaya, 2007; Armstrong, Vickers, and Zhou, 2009; Haan and
     Moraga-Gonzalez, 2011) help explain why an ad can make a product easier
     to find. Models of advertising content and attention (Anderson and
     Renault, 2006; Johnson and Myatt, 2006; Gossner, Steiner, and Stewart,
     2021) motivate the paper's distinction between a broadly appealing
     **vertical attribute** (low price) and a taste-dependent **horizontal
     attribute** (genre). Low price should weakly encourage demand broadly;
     genre can attract consumers who like it while helping others reject a
     poor match without searching.
  5. **How to measure consumer search experimentally.** Controlled lab and
     eye-tracking studies (Gabaix et al., 2006; Reutskaja et al., 2011; Shi,
     Wedel, and Pieters, 2013) measure how people acquire information and
     navigate choices. Morozov and Tuchman bring this tradition into a
     simulated online bookstore: it is remotely accessible, recruits
     thousands, delivers selected e-books, and records browsing paths. They
     present it as a more realistic, scalable way to study search while
     controlling ad exposure and content.
- **What this study adds:** The authors build a simple search model and test
  its predictions in a pre-registered, incentive-compatible bookstore
  experiment. They independently randomize ad exposure and ad content and
  observe detailed search behavior, not only final clicks or sales.
- **Replication scope:** This project reproduces selected results from Tables
  1–3 and Figures 3–5 in Morozov and Tuchman, “Where Does Advertising Content
  Lead You? We Created a Bookstore to Find Out,” *Marketing Science* 43(5),
  2024.

## 2. Data *(about 45 seconds)*

- **Sources:** The authors' public replication package combines Qualtrics
  survey responses, Google Analytics browsing events, and bookstore product
  and order data. Raw files are pinned to
  [the authors' repository revision](https://github.com/ilyamorozov/adContent/tree/b9f5c0293fc516949e9e2d294caaab57885614c7)
  and kept separate from processed data.
- **Sample construction:** The project matches survey participants to
  browsing activity and ad assignment, yielding **11,502 participants**;
  the paper reports **11,498**.
- **Setting and incentives:** The authors recruited roughly 11,500 Amazon
  Mechanical Turk participants, asked each to choose an e-book, tracked
  browsing in a simulated bookstore, and delivered selected books. The
  incentive-compatible task was designed to resemble online shopping.
- **Outcomes:** Search/purchase of the advertised book, behavior for other
  books, and stated romance and mystery ranks. Figure 5 uses **11,328**
  valid responses per genre.
- **Design:** Random assignment supports causal treatment comparisons, subject
  to accurate sample construction.

## 3. Models *(about 45 seconds)*

- **Tables 1–3:** OLS linear probability models for search and purchase;
  Table 3 also includes self-reported importance. Standard errors use the
  **HC1 robust** estimator.
- **Table 1:** For each advertised book, regress each outcome on indicators
  for plain, genre, and price ads. The omitted group is no ad, so coefficients
  are probability changes versus no ad; linear contrasts compare ad types.
- **Table 2:** Within each book and preference subgroup, compare genre-ad
  with plain-ad participants. Subgroups rank the advertised genre first or
  second through fifth; one panel pools both books.
- **Table 3:** Pool both books and compare the price-ad group with the plain-ad
  group for price outcomes, and the genre-ad group with the plain-ad group for
  genre outcomes.
- **Figures 3–5:** Figure 3 shows group means and confidence intervals; Figure
  4 shows search rates by genre rank and ad type; Figure 5 shows stated genre
  rank distributions.
- **How to read the comparisons:** Table 1's ad-versus-no-ad coefficients
  measure exposure effects; the planned contrasts and Tables 2–3 compare
  informative attribute ads with plain ads, isolating content effects.

## 4. Results and interpretation *(about 2.5 minutes)*

- **Table 1 / Figure 3 — Ads raise advertised-book search and purchase relative
  to no ad.**
  - For *Lost Girls*, price ads raise search by **9.3 percentage points**
    and purchase by **5.6 points** versus no ad (both p < .001). Plain ads
    raise them by **7.1** and **3.7 points**; genre ads by **4.8** and
    **3.1 points**.
  - For *Stateline*, all three ad types raise search by **7.2–8.6 points**
    and purchase by **5.7–6.8 points** (all p < .001 versus no ad).
    Differences between ad types are not significant.
  - Figure 3 shows search rising from about **5%** without an ad to
    **10–15%** with one; purchases rise from **2–3%** to **6–9%**. Thus,
    ads increase demand for the advertised book, but do not uniformly
    outperform other ad types.
- **Table 2 / Figure 4 — Genre information works differently by preference.**
  - In pooled results, consumers ranking the advertised genre first are
    **5.0 points more likely** to search under a genre ad than a plain ad
    (p = .005); those ranking it second through fifth are **2.4 points less
    likely** (p = .004).
  - The first-rank increase is **6.3 points** for *Stateline* (p = .009).
    For *Lost Girls*, it is **3.2 points** and not significant; the
    second-through-fifth group has a **3.5-point decrease** (p = .002).
  - Purchase differences are not significant. Figure 4 shows genre-ad search
    falling with weaker genre preference, consistent with a match-value story:
    genre information helps some consumers but can deter others.
- **Table 3 — Little evidence of spillovers to other books.**
  - Spillover estimates are small and insignificant: genre ads change
    searching for another book of that genre by **0.6 points** (p = .571)
    and purchasing one by **1.0 point** (p = .298). Filtering to the
    advertised genre is unchanged (p = .989).
- **Figure 5 — Preferences are heterogeneous.**
  - **33.8%** ranked romance fifth, while **29.5%** ranked mystery first,
    illustrating the heterogeneity behind the genre-ad results.
- Open the replicated outputs: [Table 1](./tables/table1_ad_effects.pdf),
  [Table 2](./tables/table2_genre_match_value.pdf),
  [Table 3](./tables/table3_advertising_spillovers.pdf),
  [Figure 3](./figures/figure3_ad_effects.pdf),
  [Figure 4](./figures/figure4_preference_effects.pdf), and
  [Figure 5](./figures/figure5_genre_preferences.pdf).

## 5. Conclusions and limitations *(about 30 seconds)*

- **Takeaway:** Advertising increases demand for the advertised book; genre
  ads have preference-dependent search effects; measured spillovers are small.
- **Replication caveat:** The analysis sample has 11,502 participants rather
  than the paper's 11,498. The estimates therefore reproduce the qualitative
  patterns, not an exact numerical replication of every published cell.
- **Limits:** The study covers a simulated bookstore and two books, limiting
  generalization to other products and real markets. Experimental behavior may
  not predict long-run demand; subgroup estimates are less precise.
- **Reproducibility:** The Python workflow separates data preparation and
  analyses by table/figure, preserves raw inputs, and documents setup and
  execution. Code, documentation, and outputs are in the
  [GitHub repository](https://github.com/rmrking8d/replicationprojectstat5200fall2026).
- **Closing implication:** Attribute disclosure is not universally good or
  bad. A low price can appeal broadly, while a niche genre may work best when
  the campaign targets consumers likely to value it.

### Selected literature cited in the paper

- **Advertising content and measurement:** Resnik and Stern (1977), “An
  Analysis of Information Content in Television Advertising”; Stern and
  Resnik (1991), “Information Content in Television Advertising: A
  Replication and Extension”; Abernethy and Franke (1996), “The Information
  Content of Advertising: A Meta-Analysis”; Liaukonyte, Teixeira, and Wilbur
  (2015), “Television Advertising and Online Shopping”; Du, Xu, and Wilbur
  (2019), “Immediate Responses of Online Brand Search and Price Search to TV
  Ads”; Lee, Hosanagar, and Nair (2018), “Advertising Content and Consumer
  Engagement on Social Media”; Tsai and Honka (2021), “Informational and
  Noninformational Advertising Content.”
- **Randomized ad-content evidence:** Lodish et al. (1995), “How TV
  Advertising Works: A Meta-Analysis of 389 Real World Split Cable TV
  Advertising Experiments”; Bertrand et al. (2010), “What's Advertising
  Content Worth?”; Biswas (2020), “Investigating the Effects of Including
  Discount Information in Advertising.”
- **Advertising and search:** Fong (2017), “How Targeting Affects Customer
  Search”; Honka, Hortacsu, and Vitorino (2017), “Advertising, Consumer
  Awareness, and Choice”; Nelson (1974), “Advertising as Information”;
  Milgrom and Roberts (1986), “Price and Advertising Signals of Product
  Quality.”
- **Models of ad content and search:** Anderson and Renault (2006),
  “Advertising Content”; Johnson and Myatt (2006), “On the Simple Economics
  of Advertising, Marketing, and Product Design”; Gossner, Steiner, and
  Stewart (2021), “Attention Please!”; Armstrong, Vickers, and Zhou (2009),
  “Prominence and Consumer Search.”
- **Controlled measurement of consumer search:** Gabaix et al. (2006),
  “Costly Information Acquisition”; Reutskaja et al. (2011), an eye-tracking
  study of search dynamics; and Shi, Wedel, and Pieters (2013), using
  eye-tracking data to study online information acquisition.
- **Main study:** Morozov, Ilya, and Anna Tuchman. 2024. “Where Does
  Advertising Content Lead You? We Created a Bookstore to Find Out.”
  *Marketing Science* 43(5): 986–1001.
  [Article](https://doi.org/10.1287/mksc.2023.0138).
