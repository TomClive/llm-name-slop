# LLM Character-Name Slop Blocklist

Empirical blocklist of character names LLMs overuse in fiction, built by
sampling story openings from multiple models via `fal-ai/any-llm` and
comparing name frequencies against human baselines (SSA baby names for first
names, US Census 2010 for surnames).

## Usage

```
pip install -r requirements.txt

python run.py sample --dry-run      # print prompts, no API calls
python run.py sample --smoke-test   # 3 samples, first model only
python run.py sample                # full sweep (config.MODELS x SAMPLES_PER_MODEL)
python run.py analyze               # extract names, compute lift, write outputs

# robustness: neutral / role-reversed prompts, written to samples_<variant>/
python run.py sample --variant neutral --n 40
python run.py sample --variant reversed_roles --n 40
```

Needs `FAL_KEY` in the environment (falls back to `HKCU\Environment` on
Windows). All knobs live in `config.py`. Sampling appends to
`output/samples/{model}.jsonl` incrementally and resumes where it left off.

## Outputs (`output/`)

- `samples/{model}.jsonl` — raw completions with genre/theme/prompt/timestamp
- `name_counts.csv` — per-name counts, per model + pooled, human_freq, lift,
  lift 95% CI, `unstable` flag
- `blocklist.json` — `{"first_names": [...], "surnames": [...]}` with lift,
  lift CI, tier (real/invented), `unstable`, n_genres, baseline_count
- `report.md` — data-quality (coverage + truncation), tiered blocklist,
  per-model top-20, gender, protagonist-vs-secondary roles, genre notes
- `gender_breakdown.json`, `role_breakdown.json` — machine-readable gender and
  narrative-role stats
- `heatmap.html` — per-model slop heatmap
- `article.md` — the writeup

## Method notes

- `lift = llm_freq / human_freq`, add-one smoothed. Names split into **real**
  (in the human baseline; lift is a true over-use ratio) and **invented** (no
  baseline; lift is floored, so ranked by frequency).
- `max_tokens=80` truncates many completions; see the Data-quality section of
  `report.md` for per-model truncation rates and the truncation robustness check.
- Extraction: spaCy PERSON NER + gazetteer rescue, with filters for possessives,
  place/building spans, professional vs kinship/role titles.
