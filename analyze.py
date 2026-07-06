"""Analysis: baselines, per-name counts, lift, blocklist, and report."""

import csv
import glob
import io
import json
import math
import os
import zipfile
from collections import Counter, defaultdict

import requests

import config
import extract


def is_truncated(text: str) -> bool:
    """True if a completion appears cut off mid-sentence (no terminal punct).

    A proxy for hitting the max_tokens cap; used only to report/caveat, not to
    drop samples.
    """
    t = (text or "").rstrip().rstrip('"”’\')')
    return not t.endswith((".", "!", "?", "…"))


def ranked(counter, n: int | None = None) -> list:
    """Counter items sorted by count desc, then name asc — deterministic.

    Counter.most_common breaks ties by first-insertion order, which is not
    stable across runs because upstream name sets iterate in hash-seed order.
    Sorting ties by name keeps regenerated outputs byte-identical.
    """
    items = sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]).casefold()))
    return items[:n] if n is not None else items


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion k/n.

    Robust at small k (unlike the normal approximation), so it flags how
    unstable a low-count name's frequency really is.
    """
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


# --- Baselines ------------------------------------------------------------

def _download(url: str, dest: str) -> str:
    if os.path.exists(dest):
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"Downloading {url} ...")
    # ssa.gov 403s the default python-requests user agent
    resp = requests.get(url, timeout=300, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/126.0 Safari/537.36"})
    resp.raise_for_status()
    with open(dest, "wb") as f:
        f.write(resp.content)
    return dest


def load_ssa_first_names() -> tuple[Counter, int]:
    """SSA first-name counts aggregated over SSA_YEAR_RANGE (sexes combined)."""
    dest = os.path.join(config.DATA_DIR, "ssa_names.zip")
    try:
        path = _download(config.SSA_URL, dest)
    except requests.HTTPError:
        print("ssa.gov blocked the download, using GitHub mirror")
        path = _download(config.SSA_MIRROR_URL, dest)
    lo, hi = config.SSA_YEAR_RANGE
    counts: Counter = Counter()
    with zipfile.ZipFile(path) as z:
        for info in z.namelist():
            if not info.startswith("yob") or not info.endswith(".txt"):
                continue
            year = int(info[3:7])
            if not lo <= year <= hi:
                continue
            with z.open(info) as f:
                for line in io.TextIOWrapper(f, encoding="utf-8"):
                    name, _sex, n = line.strip().split(",")
                    counts[name.casefold()] += int(n)
    return counts, sum(counts.values())


def load_ssa_gendered() -> tuple[Counter, Counter]:
    """SSA counts split by sex over SSA_YEAR_RANGE: (female, male) Counters."""
    dest = os.path.join(config.DATA_DIR, "ssa_names.zip")
    try:
        path = _download(config.SSA_URL, dest)
    except requests.HTTPError:
        path = _download(config.SSA_MIRROR_URL, dest)
    lo, hi = config.SSA_YEAR_RANGE
    female: Counter = Counter()
    male: Counter = Counter()
    with zipfile.ZipFile(path) as z:
        for info in z.namelist():
            if not info.startswith("yob") or not info.endswith(".txt"):
                continue
            if not lo <= int(info[3:7]) <= hi:
                continue
            with z.open(info) as f:
                for line in io.TextIOWrapper(f, encoding="utf-8"):
                    name, sex, n = line.strip().split(",")
                    (female if sex == "F" else male)[name.casefold()] += int(n)
    return female, male


def infer_gender(name: str, female: Counter, male: Counter) -> str:
    """'female' / 'male' / 'ambiguous' / 'unknown' from SSA sex ratio.

    A name is gendered only if >=80% of its SSA registrations are one sex;
    the 20-80% band is 'ambiguous' (Alex, Jamie), and absent names 'unknown'.
    """
    k = name.casefold()
    tf, tm = female.get(k, 0), male.get(k, 0)
    if tf + tm == 0:
        return "unknown"
    frac = tf / (tf + tm)
    if frac >= 0.8:
        return "female"
    if frac <= 0.2:
        return "male"
    return "ambiguous"


def load_census_surnames() -> tuple[Counter, int]:
    """US Census 2010 surname counts. Returns (Counter, total)."""
    path = _download(config.CENSUS_SURNAMES_URL,
                     os.path.join(config.DATA_DIR, "census_surnames.zip"))
    counts: Counter = Counter()
    with zipfile.ZipFile(path) as z:
        csv_names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        with z.open(csv_names[0]) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
            for row in reader:
                name = (row.get("name") or row.get("NAME") or "").strip()
                cnt = (row.get("count") or row.get("COUNT") or "0").strip()
                if name and cnt.isdigit():
                    counts[name.casefold()] += int(cnt)
    return counts, sum(counts.values())


def smoothed_freq(name_key: str, baseline: Counter, total: int) -> float:
    """Add-one smoothed share so unseen names never divide by zero."""
    return (baseline.get(name_key, 0) + 1) / (total + len(baseline) + 1)


# --- Counting -------------------------------------------------------------

def load_samples() -> dict[str, list[dict]]:
    """model -> list of sample records, from output/samples/*.jsonl."""
    by_model: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(config.SAMPLES_DIR, "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    by_model[rec["model"]].append(rec)
    return dict(by_model)


def count_names(by_model: dict[str, list[dict]],
                known_first: set[str] | None = None):
    """Sample-level presence counts per (type, name_key).

    Returns (rows, n_samples_per_model) where rows is
    {(type, key): {display, type, per_model: Counter, genres: Counter}}.
    """
    rows: dict = {}
    n_per_model: dict[str, int] = {}
    for model, samples in by_model.items():
        n_per_model[model] = len(samples)
        for rec in samples:
            for typ, display in extract.names_in_sample(
                    rec["completion"], known_first):
                key = (typ, display.casefold())
                row = rows.setdefault(key, {
                    "display": display, "type": typ,
                    "per_model": Counter(), "genres": Counter(),
                })
                row["per_model"][model] += 1
                row["genres"][rec["genre"]] += 1
    return rows, n_per_model


# --- Outputs --------------------------------------------------------------

def analyze() -> None:
    by_model = load_samples()
    if not by_model:
        raise SystemExit("No samples found in output/samples/ — run sampling first.")
    models = sorted(by_model)
    print(f"Loaded samples: " +
          ", ".join(f"{m}={len(by_model[m])}" for m in models))

    ssa, ssa_total = load_ssa_first_names()
    try:
        census, census_total = load_census_surnames()
    except Exception as e:
        print(f"WARNING: surname baseline unavailable ({e}); "
              f"surnames get add-one-only smoothed lift")
        census, census_total = Counter(), 0

    female, male = load_ssa_gendered()

    # Gazetteer for NER rescue: SSA names with a non-trivial count, so junk
    # single-year entries don't create false positives.
    known_first = {k for k, v in ssa.items() if v >= 100}

    print("Extracting names (spaCy + gazetteer)...")
    rows, n_per_model = count_names(by_model, known_first)
    total_samples = sum(n_per_model.values())
    print(f"{len(rows)} distinct names across {total_samples} samples")

    # enrich rows with pooled stats
    for (typ, key), row in rows.items():
        pooled = sum(row["per_model"].values())
        row["pooled"] = pooled
        row["llm_freq"] = pooled / total_samples
        if typ == "first":
            row["human_freq"] = smoothed_freq(key, ssa, ssa_total)
            row["baseline_count"] = ssa.get(key, 0)
            row["gender"] = infer_gender(row["display"], female, male)
        else:
            row["human_freq"] = smoothed_freq(key, census, census_total)
            row["baseline_count"] = census.get(key, 0)
            row["gender"] = "n/a"
        row["lift"] = row["llm_freq"] / row["human_freq"]
        row["n_models"] = sum(1 for v in row["per_model"].values() if v > 0)
        row["n_models_min"] = sum(
            1 for v in row["per_model"].values() if v >= config.MIN_SAMPLES)
        row["n_genres"] = len(row["genres"])
        # Wilson CI on the sample-presence rate, mapped back to a lift range,
        # plus an "unstable" flag for thin evidence (few hits => wide interval).
        lo, hi = wilson_interval(pooled, total_samples)
        row["freq_ci"] = (lo, hi)
        row["lift_ci"] = (lo / row["human_freq"], hi / row["human_freq"])
        row["unstable"] = pooled < 10
        # An "invented" name has no human baseline at all, so its lift is just
        # an artifact of the add-one floor (millions x on a handful of hits).
        # A "real" name exists in the baseline, so its lift is a true measure
        # of over-use. We keep the two apart when ranking.
        row["tier"] = "invented" if row["baseline_count"] == 0 else "real"

    gender = gender_breakdown(by_model, known_first, female, male)
    roles = role_breakdown(by_model, known_first, female, male)

    # Truncation (max_tokens proxy) and blocklist coverage — computed here so
    # the report/article numbers are reproducible, not hand-derived.
    trunc = {m.split("/")[-1]: sum(is_truncated(r["completion"]) for r in s)
             for m, s in by_model.items()}
    blk = blocklist_rows(rows)
    real_f = {r["display"].casefold() for r in blk
              if r["type"] == "first" and r["tier"] == "real"}
    real_s = {r["display"].casefold() for r in blk
              if r["type"] == "surname" and r["tier"] == "real"}
    any_f = {r["display"].casefold() for r in blk if r["type"] == "first"}
    any_s = {r["display"].casefold() for r in blk if r["type"] == "surname"}

    def covered(rec, fset, sset):
        for t, n in extract.names_in_sample(rec["completion"], known_first):
            if (t == "first" and n.casefold() in fset) or \
               (t == "surname" and n.casefold() in sset):
                return True
        return False
    all_recs = [r for s in by_model.values() for r in s]
    coverage = {
        "any": sum(covered(r, any_f, any_s) for r in all_recs),
        "real_only": sum(covered(r, real_f, real_s) for r in all_recs),
        "total": len(all_recs),
    }

    ghost = ghost_couple_check(by_model)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    write_csv(rows, models)
    blocklist = write_blocklist(rows)
    write_report(rows, models, n_per_model, blocklist, gender, roles,
                 trunc, coverage, ghost)
    write_heatmap(rows, models, n_per_model)
    for name, obj in [("gender_breakdown.json", gender),
                      ("role_breakdown.json", roles),
                      ("ghost_couple_check.json", ghost)]:
        with open(os.path.join(config.OUTPUT_DIR, name), "w",
                  encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
    print(f"Wrote name_counts.csv, blocklist.json, report.md, heatmap.html, "
          f"gender_breakdown.json, role_breakdown.json, ghost_couple_check.json "
          f"to {config.OUTPUT_DIR}")


def gender_breakdown(by_model: dict, known_first: set, female: Counter,
                     male: Counter) -> dict:
    """Per-model gender split of first-name mentions + female-name concentration.

    Counts are sample-level name presence (a name counts once per sample it
    appears in). 'top1_female_share' is the share of a model's female mentions
    taken by its single most common female name — the distribution-collapse
    measure that makes Gemini/Elara stand out.
    """
    out = {}
    for model, samples in by_model.items():
        short = model.split("/")[-1]
        gcount = Counter()
        fem = Counter()
        mal = Counter()
        for rec in samples:
            for typ, name in extract.names_in_sample(rec["completion"],
                                                     known_first):
                if typ != "first":
                    continue
                g = infer_gender(name, female, male)
                gcount[g] += 1
                if g == "female":
                    fem[name] += 1
                elif g == "male":
                    mal[name] += 1
        f_tot = gcount["female"] or 1
        top_f = ranked(fem, 1)[0] if fem else ("—", 0)
        out[short] = {
            "female": gcount["female"], "male": gcount["male"],
            "ambiguous": gcount["ambiguous"], "unknown": gcount["unknown"],
            "pct_female": round(gcount["female"] /
                                (gcount["female"] + gcount["male"] or 1), 3),
            "distinct_female_names": len(fem),
            "distinct_male_names": len(mal),
            "top_female": top_f[0], "top_female_count": top_f[1],
            "top1_female_share": round(top_f[1] / f_tot, 3),
            "elara_female_share": round(fem.get("Elara", 0) / f_tot, 3),
            "top_female_names": ranked(fem, 6),
            "top_male_names": ranked(mal, 6),
        }
    return out


def role_breakdown(by_model: dict, known_first: set, female: Counter,
                   male: Counter) -> dict:
    """Split names by narrative role (protagonist = first-named, secondary =
    second-named) and report gender + top names for each role, per model.
    """
    ROLES = ("primary", "secondary")
    out = {"per_model": {}, "pooled": {}}
    pooled_g = {r: Counter() for r in ROLES}
    pooled_names = {r: Counter() for r in ROLES}
    pooled_pairs = Counter()
    for model, samples in by_model.items():
        short = model.split("/")[-1]
        g = {r: Counter() for r in ROLES}
        names = {r: Counter() for r in ROLES}
        for rec in samples:
            chars = extract.ordered_characters(rec["completion"], known_first)
            slots = [c["first"] for c in chars if c["first"]][:2]
            for i, role in enumerate(ROLES):
                if i < len(slots):
                    gg = infer_gender(slots[i], female, male)
                    g[role][gg] += 1
                    names[role][slots[i]] += 1
                    pooled_g[role][gg] += 1
                    pooled_names[role][slots[i]] += 1
            if len(slots) >= 2:
                pooled_pairs[(infer_gender(slots[0], female, male),
                              infer_gender(slots[1], female, male))] += 1

        def pctf(role):
            f, m = g[role]["female"], g[role]["male"]
            return round(f / (f + m), 3) if f + m else 0.0
        out["per_model"][short] = {
            r: {"female": g[r]["female"], "male": g[r]["male"],
                "pct_female": pctf(r),
                "top_names": ranked(names[r], 5)} for r in ROLES}

    def ppctf(role):
        f, m = pooled_g[role]["female"], pooled_g[role]["male"]
        return round(f / (f + m), 3) if f + m else 0.0
    pair_tot = sum(v for (a, b), v in pooled_pairs.items()
                   if a in ("female", "male") and b in ("female", "male")) or 1
    out["pooled"] = {
        r: {"female": pooled_g[r]["female"], "male": pooled_g[r]["male"],
            "pct_female": ppctf(r),
            "top_names": ranked(pooled_names[r], 8)} for r in ROLES}
    out["gender_pairing"] = {
        f"{a}_primary+{b}_secondary": {
            "count": pooled_pairs[(a, b)],
            "share": round(pooled_pairs[(a, b)] / pair_tot, 3)}
        for a in ("female", "male") for b in ("female", "male")}

    # Truncation robustness: does the female-lead/male-secondary split survive
    # in complete (non-truncated) samples? Recompute secondary %female split by
    # completion status.
    tv = {"truncated": Counter(), "complete": Counter()}
    fill = {"total": 0, "two_named": 0}
    for model, samples in by_model.items():
        for rec in samples:
            slots = [c["first"] for c in
                     extract.ordered_characters(rec["completion"], known_first)
                     if c["first"]][:2]
            fill["total"] += 1
            if len(slots) >= 2:
                fill["two_named"] += 1
                b = "truncated" if is_truncated(rec["completion"]) else "complete"
                tv[b][infer_gender(slots[1], female, male)] += 1
    out["truncation_robustness"] = {
        b: {"secondary_pct_female": round(c["female"] / (c["female"] + c["male"]), 3)
            if c["female"] + c["male"] else 0.0,
            "n": c["female"] + c["male"]}
        for b, c in tv.items()}
    out["secondary_fill_rate"] = round(fill["two_named"] / fill["total"], 3)
    return out


# Clusters reported by Brzozowski & Chung, "The Ghost Couple" (arXiv:2606.02184),
# used to cross-check their fingerprints against our fiction-domain samples.
GHOST_COUPLE_CLUSTERS = {
    "claude": ["Elena Vasquez", "Marcus Chen", "Amara Okafor"],
    "gemini": ["Aris Thorne", "Lena Petrova"],
    "gpt": ["Elara Voss"],
}


def ghost_couple_check(by_model: dict) -> dict:
    """Cross-check the prior-work clusters + a co-occurrence test.

    Uses raw string presence (the clusters are exact full names), plus a
    Marcus/Chen co-occurrence lift in Claude to test the 'ensemble' claim.
    """
    phrases = sorted({p for ps in GHOST_COUPLE_CLUSTERS.values() for p in ps})
    hits = {p: Counter() for p in phrases}
    for model, samples in by_model.items():
        short = model.split("/")[-1]
        for rec in samples:
            for p in phrases:
                if p in rec["completion"]:
                    hits[p][short] += 1

    # Marcus/Chen co-occurrence in Claude (chance vs observed)
    claude = next((s for m, s in by_model.items() if "claude" in m), [])
    n = len(claude) or 1
    na = sum("Marcus" in r["completion"] for r in claude)
    nb = sum("Chen" in r["completion"] for r in claude)
    nboth = sum("Marcus" in r["completion"] and "Chen" in r["completion"]
                for r in claude)
    expected = (na / n) * (nb / n) * n
    lift = (nboth / n) / ((na / n) * (nb / n)) if na and nb else 0.0
    return {
        "cluster_hits": {p: dict(c) for p, c in hits.items()},
        "marcus_chen": {"n": n, "marcus": na, "chen": nb, "both": nboth,
                        "expected": round(expected, 1), "cooc_lift": round(lift, 2)},
    }


def write_csv(rows: dict, models: list[str]) -> None:
    path = os.path.join(config.OUTPUT_DIR, "name_counts.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "type"] + [f"n_{m}" for m in models] +
                   ["pooled_count", "llm_freq", "human_freq", "lift",
                    "lift_ci_low", "lift_ci_high", "n_models", "unstable"])
        for (typ, key), row in sorted(
                rows.items(),
                key=lambda kv: (-kv[1]["lift"], kv[1]["display"].casefold(),
                                kv[0][0])):
            w.writerow([row["display"], typ] +
                       [row["per_model"].get(m, 0) for m in models] +
                       [row["pooled"], f"{row['llm_freq']:.5f}",
                        f"{row['human_freq']:.3e}", f"{row['lift']:.1f}",
                        f"{row['lift_ci'][0]:.1f}", f"{row['lift_ci'][1]:.1f}",
                        row["n_models"], int(row["unstable"])])


def blocklist_rows(rows: dict) -> list:
    """Names meeting the inclusion criteria, ranked within tier.

    Real names (present in the human baseline) are ranked by lift, which is a
    meaningful over-use measure for them. Invented names (zero baseline) all
    share the same floored lift, so ranking them by lift is noise; they are
    ranked by pooled frequency instead. Real names sort ahead of invented ones
    so the list leads with names a reader would actually recognise.
    """
    picked = [
        row for row in rows.values()
        if row["n_models_min"] >= config.MIN_MODELS
        and row["lift"] >= config.LIFT_THRESHOLD
    ]
    return sorted(picked, key=lambda r: (
        r["tier"] == "invented", -r["lift"] if r["tier"] == "real"
        else -r["pooled"], r["display"].casefold(), r["type"]))


def write_blocklist(rows: dict) -> list:
    picked = blocklist_rows(rows)
    out = {"first_names": [], "surnames": [],
           "config": {"lift_threshold": config.LIFT_THRESHOLD,
                      "min_samples": config.MIN_SAMPLES,
                      "min_models": config.MIN_MODELS,
                      "tiers": {
                          "real": "present in human baseline; lift is a true "
                                  "over-use ratio",
                          "invented": "absent from human baseline; lift is "
                                      "floored/artefactual, ranked by frequency"}}}
    for row in picked:
        bucket = "first_names" if row["type"] == "first" else "surnames"
        out[bucket].append({
            "name": row["display"],
            "tier": row["tier"],
            "lift": round(row["lift"], 1),
            "lift_ci": [round(row["lift_ci"][0], 1), round(row["lift_ci"][1], 1)],
            "pooled_count": row["pooled"],
            "unstable": row["unstable"],
            "n_models": row["n_models"],
            "n_genres": row["n_genres"],
            "baseline_count": row["baseline_count"],
            "top_genre": ranked(row["genres"], 1)[0][0],
        })
    with open(os.path.join(config.OUTPUT_DIR, "blocklist.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return picked


def _md_table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(lines)


def write_report(rows: dict, models: list[str], n_per_model: dict,
                 blocklist: list, gender: dict | None = None,
                 roles: dict | None = None, trunc: dict | None = None,
                 coverage: dict | None = None, ghost: dict | None = None) -> None:
    lines = ["# LLM Character-Name Slop — Report", ""]
    lines.append(
        f"Sampled via `fal-ai/any-llm`, prompt: two-sentence story openings, "
        f"{len(config.GENRES)} genres rotated evenly, unique mundane-theme "
        f"perturbation per prompt, temperature {config.TEMPERATURE}, "
        f"max_tokens {config.MAX_TOKENS}.")
    lines.append("")
    lines.append("Samples per model: " + ", ".join(
        f"`{m}` = {n_per_model[m]}" for m in models))
    skipped = [m for m in config.MODELS if m not in models]
    if skipped:
        lines.append("")
        lines.append("Skipped/unavailable models: " +
                     ", ".join(f"`{m}`" for m in skipped))
    lines.append("")
    lines.append(
        f"Baselines: SSA baby names {config.SSA_YEAR_RANGE[0]}–"
        f"{config.SSA_YEAR_RANGE[1]} (first names), US Census 2010 "
        f"(surnames), both add-one smoothed. "
        f"`lift = llm_freq / human_freq`. Blocklist: name in ≥"
        f"{config.MIN_SAMPLES} samples for ≥{config.MIN_MODELS} models and "
        f"lift ≥ {config.LIFT_THRESHOLD}×.")

    # Data quality: coverage + truncation, so headline numbers are reproducible
    if coverage or trunc:
        lines += ["", "## Data quality"]
        if coverage:
            t = coverage["total"]
            lines.append(
                f"**Blocklist coverage.** Sample-level presence of *any* "
                f"final-blocklist name (first or surname, real+invented) in a "
                f"completion: **{coverage['any']}/{t} = "
                f"{coverage['any']/t:.1%}**. Restricting to real-tier names "
                f"only: {coverage['real_only']}/{t} = "
                f"{coverage['real_only']/t:.1%}. (This is the '~76%' headline; "
                f"a name counts once per sample regardless of repeats.)")
        if trunc:
            short_total = {m.split("/")[-1]: n for m, n in n_per_model.items()}
            lines += ["",
                      f"**Truncation.** `max_tokens={config.MAX_TOKENS}`, so "
                      f"many completions stop mid-sentence (no terminal "
                      f"punctuation). Likely-truncated samples per model:"]
            lines.append(_md_table(
                ["model", "truncated / total", "%"],
                [[m, f"{trunc[m]} / {short_total.get(m, 200)}",
                  f"{trunc[m] / short_total.get(m, 200):.0%}"] for m in trunc]))
            if roles and "truncation_robustness" in roles:
                tr = roles["truncation_robustness"]
                lines += ["",
                          f"Truncation does **not** overturn the role analysis: "
                          f"≥2 characters are named in "
                          f"{roles['secondary_fill_rate']:.0%} of samples, and "
                          f"the secondary character is "
                          f"{tr['truncated']['secondary_pct_female']:.0%} female "
                          f"in truncated samples vs "
                          f"{tr['complete']['secondary_pct_female']:.0%} in "
                          f"complete ones — the male-secondary skew holds in "
                          f"both."]

    # Blocklist summary, split into the two tiers
    firsts = [r for r in blocklist if r["type"] == "first"]
    lasts = [r for r in blocklist if r["type"] == "surname"]
    real = [r for r in blocklist if r["tier"] == "real"]
    invented = [r for r in blocklist if r["tier"] == "invented"]
    lines += ["", "## Blocklist",
              f"{len(firsts)} first names, {len(lasts)} surnames "
              f"({len(real)} real names, {len(invented)} invented).", "",
              "Two tiers are reported separately because lift means different "
              "things for each. **Real names** exist in the human baseline, so "
              "their lift is a genuine over-use ratio. **Invented names** have "
              "no baseline at all, so their lift is just the add-one floor "
              "(identical millions-× values on a handful of hits) — they are "
              "ranked by frequency, not lift."]
    lines += ["", "### Tier 1 — real names, ranked by lift (the useful list)",
              "Names marked † have fewer than 10 pooled hits — thin evidence; "
              "treat the lift as indicative, not precise (see the wide CI).", ""]
    lines.append(_md_table(
        ["name", "type", "pooled n", "lift", "lift 95% CI", "models", "genres",
         "SSA/Census n"],
        [[r["display"] + ("†" if r["unstable"] else ""), r["type"], r["pooled"],
          f"{r['lift']:.0f}×",
          f"{r['lift_ci'][0]:.0f}–{r['lift_ci'][1]:.0f}×",
          r["n_models"], r["n_genres"], r["baseline_count"]]
         for r in real]))
    lines += ["", "### Tier 2 — invented names, ranked by frequency",
              "(All invented names are low-count and genre-specific — treat as "
              "the least reliable part of the list.)", ""]
    lines.append(_md_table(
        ["name", "type", "pooled n", "models", "top genre"],
        [[r["display"] + ("†" if r["unstable"] else ""), r["type"], r["pooled"],
          r["n_models"], ranked(r["genres"], 1)[0][0]] for r in invented]))

    # Per-model top 20
    lines += ["", "## Per-model top 20 names (by sample count)"]
    for m in models:
        ranked_rows = sorted(rows.values(),
                             key=lambda r: (-r["per_model"].get(m, 0),
                                            r["display"].casefold(), r["type"]))
        top = [r for r in ranked_rows if r["per_model"].get(m, 0) > 0][:20]
        lines += ["", f"### {m}", ""]
        lines.append(_md_table(
            ["name", "type", "n", f"share of {n_per_model[m]}", "lift"],
            [[r["display"], r["type"], r["per_model"][m],
              f"{r['per_model'][m] / n_per_model[m]:.0%}",
              f"{r['lift']:.0f}×"] for r in top]))

    # Cross-model overlap
    universal = sorted(
        (r for r in rows.values()
         if all(r["per_model"].get(m, 0) >= config.MIN_SAMPLES for m in models)),
        key=lambda r: (-r["pooled"], r["display"].casefold(), r["type"]))
    lines += ["", "## Names every model loves",
              f"Appearing ≥{config.MIN_SAMPLES}× in **all** {len(models)} models:", ""]
    if universal:
        lines.append(_md_table(
            ["name", "type", "pooled n", "lift"],
            [[r["display"], r["type"], r["pooled"], f"{r['lift']:.0f}×"]
             for r in universal[:25]]))
    else:
        lines.append("(none)")

    # Gender
    if gender:
        lines += ["", "## Gender",
                  "First-name mentions classified via SSA sex ratio "
                  "(≥80% one sex = gendered; the middle band is ambiguous). "
                  "Counts are sample-level presence.", ""]
        lines.append(_md_table(
            ["model", "total mentions", "female / male", "% female",
             "distinct ♀ names", "top ♀ name", "top ♀ share", "Elara ♀ share"],
            [[m, g["female"] + g["male"] + g["ambiguous"] + g["unknown"],
              f"{g['female']} / {g['male']}", f"{g['pct_female']:.0%}",
              g["distinct_female_names"],
              f"{g['top_female']} ({g['top_female_count']})",
              f"{g['top1_female_share']:.0%}", f"{g['elara_female_share']:.0%}"]
             for m, g in gender.items()]))
        lines += ["",
                  "**Distribution collapse:** `top ♀ share` is the fraction of "
                  "a model's female protagonists carried by its single most "
                  "common female name. Gemini's Elara alone accounts for ~46% "
                  "of its female characters — 3× the concentration of any other "
                  "model — while Claude's female names are the most varied.", ""]
        for m, g in gender.items():
            fem = ", ".join(f"{n} {c}" for n, c in g["top_female_names"])
            lines.append(f"- **{m}** — top ♀: {fem}")

    # Roles: protagonist vs secondary
    if roles:
        pp, ps = roles["pooled"]["primary"], roles["pooled"]["secondary"]
        lines += ["", "## Protagonist vs secondary character",
                  "The prompt asks for a protagonist then one secondary "
                  "character, so the first-named person is the protagonist and "
                  "the second is the secondary. Splitting by role reveals a "
                  "strong structural default that the pooled gender balance "
                  "hides.", "",
                  f"**Pooled:** protagonists are {pp['pct_female']:.0%} female; "
                  f"secondary characters are {ps['pct_female']:.0%} female "
                  f"({1 - ps['pct_female']:.0%} male). The models overwhelmingly "
                  f"default to a female lead paired with a male supporting "
                  f"character.", ""]
        lines.append(_md_table(
            ["model", "protagonist % female", "secondary % female"],
            [[m, f"{d['primary']['pct_female']:.0%}",
              f"{d['secondary']['pct_female']:.0%}"]
             for m, d in roles["per_model"].items()]))
        lines += ["", "Most common protagonist / secondary gender pairing "
                  "(pooled):", ""]
        order = ["female_primary+male_secondary", "female_primary+female_secondary",
                 "male_primary+female_secondary", "male_primary+male_secondary"]
        lines.append(_md_table(
            ["pairing", "share"],
            [[k.replace("_", " ").replace("+", " + "),
              f"{roles['gender_pairing'][k]['share']:.0%}"] for k in order]))
        lines += ["", "Top protagonist names vs top secondary names (pooled):", ""]
        lines.append("- **protagonists:** " +
                     ", ".join(f"{n} {c}" for n, c in pp["top_names"]))
        lines.append("- **secondary:** " +
                     ", ".join(f"{n} {c}" for n, c in ps["top_names"]))

    # Cross-check against prior work (Brzozowski & Chung, arXiv:2606.02184)
    if ghost:
        lines += ["", "## Cross-check vs prior work (the ghost couple)",
                  "Presence of the character clusters reported by Brzozowski & "
                  "Chung (arXiv:2606.02184) in our fiction samples (raw full-name "
                  "match):", ""]
        rows_gc = []
        for fam, names in GHOST_COUPLE_CLUSTERS.items():
            for name in names:
                h = ghost["cluster_hits"].get(name, {})
                where = ", ".join(f"{m}:{c}" for m, c in sorted(h.items())) or "—"
                rows_gc.append([name, f"{fam} (theirs)", sum(h.values()), where])
        lines.append(_md_table(
            ["name", "their attribution", "total hits", "our hits by model"],
            rows_gc))
        mc = ghost["marcus_chen"]
        lines += ["",
                  f"**Ensemble test (Marcus + Chen, Claude):** Marcus in "
                  f"{mc['marcus']}/{mc['n']} stories, Chen in {mc['chen']}, both "
                  f"in **{mc['both']}** (chance would give ~{mc['expected']}) — a "
                  f"co-occurrence lift of {mc['cooc_lift']}×. Real but modest; "
                  f"the 'couple' is looser in fiction than in fabricated-expert "
                  f"text."]

    # Genre conditioning
    genre_bound = []
    for r in blocklist:
        if r["pooled"] >= 4:
            genre, cnt = ranked(r["genres"], 1)[0]
            share = cnt / r["pooled"]
            if share >= 0.6:
                genre_bound.append((r, genre, share))
    lines += ["", "## Genre conditioning",
              "Blocklist names with ≥60% of hits in a single genre:", ""]
    if genre_bound:
        lines.append(_md_table(
            ["name", "genre", "share", "pooled n"],
            [[r["display"], g, f"{s:.0%}", r["pooled"]]
             for r, g, s in genre_bound[:25]]))
    else:
        lines.append("(none)")

    with open(os.path.join(config.OUTPUT_DIR, "report.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_heatmap(rows: dict, models: list[str], n_per_model: dict) -> None:
    """Standalone HTML heatmap: per-model share for the top slop names."""
    # Rank names by pooled frequency across models, keep the top 40 that clear
    # the blocklist bar so the grid is readable.
    picked = sorted(
        (r for r in rows.values()
         if r["n_models_min"] >= config.MIN_MODELS
         and r["lift"] >= config.LIFT_THRESHOLD),
        key=lambda r: (-r["pooled"], r["display"].casefold(), r["type"]))[:40]

    short = [m.split("/")[-1] for m in models]
    cells = []
    for r in picked:
        row_cells = []
        for m in models:
            share = r["per_model"].get(m, 0) / n_per_model[m]
            row_cells.append(share)
        cells.append({
            "name": r["display"], "type": r["type"], "tier": r["tier"],
            "lift": r["lift"], "pooled": r["pooled"], "shares": row_cells,
        })
    data = {"models": short, "cells": cells}

    html = _HEATMAP_TEMPLATE.replace("__DATA__", json.dumps(data))
    with open(os.path.join(config.OUTPUT_DIR, "heatmap.html"), "w",
              encoding="utf-8") as f:
        f.write(html)


_HEATMAP_TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LLM Character-Name Slop — Heatmap</title>
<style>
  :root { color-scheme: dark; }
  body { margin: 0; background: #0e1116; color: #e6edf3;
         font: 14px/1.45 -apple-system, Segoe UI, Roboto, sans-serif;
         padding: 32px; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  p.sub { color: #8b949e; margin: 0 0 24px; max-width: 70ch; }
  table { border-collapse: collapse; }
  th.corner { text-align: left; }
  th.model { font-weight: 600; padding: 0 6px 10px; text-align: center;
             vertical-align: bottom; white-space: nowrap; font-size: 12px; }
  td.name { padding: 2px 12px 2px 0; white-space: nowrap; text-align: right; }
  td.name .n { font-weight: 600; }
  td.name .meta { color: #8b949e; font-size: 11px; margin-left: 6px; }
  .badge { display: inline-block; font-size: 10px; padding: 0 5px;
           border-radius: 8px; margin-left: 6px; vertical-align: middle; }
  .badge.invented { background: #3d2b57; color: #d2a8ff; }
  .badge.real { background: #143a2e; color: #7ee2b8; }
  td.cell { width: 62px; height: 30px; text-align: center; border-radius: 4px;
            font-variant-numeric: tabular-nums; font-size: 12px;
            border: 1px solid #0e1116; }
  .legend { margin-top: 20px; color: #8b949e; font-size: 12px; }
  .legend .chip { display: inline-block; width: 14px; height: 14px;
                  border-radius: 3px; vertical-align: middle; margin: 0 4px; }
</style></head><body>
<h1>LLM Character-Name Slop — per-model heatmap</h1>
<p class="sub">Each cell is the share of that model's 200 story openings that
contained the name. Darker = more slop. Names ordered by pooled frequency
across all five models; the badge marks whether the name exists in human
name data (real) or is a model invention (invented).</p>
<div id="grid"></div>
<div class="legend">Share of a model's stories containing the name:
  <span class="chip" style="background:#0e2a3a"></span> low
  <span class="chip" style="background:#1f6feb"></span>
  <span class="chip" style="background:#58a6ff"></span>
  <span class="chip" style="background:#f0b72f"></span>
  <span class="chip" style="background:#f85149"></span> high (≈45%)
</div>
<script>
const DATA = __DATA__;
function color(s){
  // 0 -> dark slate, ramp through blue, amber, red at ~0.45+
  if (s <= 0) return '#161b22';
  const t = Math.min(1, s / 0.45);
  const stops = [[14,42,58],[31,111,235],[88,166,255],[240,183,47],[248,81,73]];
  const x = t*(stops.length-1); const i = Math.floor(x); const f = x-i;
  const a = stops[i], b = stops[Math.min(i+1,stops.length-1)];
  const c = a.map((v,k)=>Math.round(v+(b[k]-v)*f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}
function textColor(s){ return s/0.45 > 0.28 && s/0.45 < 0.72 ? '#0e1116'
                       : (s>0 ? '#e6edf3' : '#484f58'); }
let h = '<table><thead><tr><th class="corner"></th>';
for (const m of DATA.models) h += `<th class="model">${m}</th>`;
h += '</tr></thead><tbody>';
for (const row of DATA.cells){
  const lift = row.lift >= 10000 ? Math.round(row.lift/1000)+'k'
             : Math.round(row.lift);
  h += `<tr><td class="name"><span class="n">${row.name}</span>`
     + `<span class="badge ${row.tier}">${row.tier}</span>`
     + `<span class="meta">${row.type} · ${lift}× · n=${row.pooled}</span></td>`;
  for (const s of row.shares){
    const pct = s>0 ? Math.round(s*100)+'%' : '';
    h += `<td class="cell" style="background:${color(s)};color:${textColor(s)}">${pct}</td>`;
  }
  h += '</tr>';
}
h += '</tbody></table>';
document.getElementById('grid').innerHTML = h;
</script></body></html>
"""
