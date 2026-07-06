# LLM Character-Name Slop — Report

Sampled via `fal-ai/any-llm`, prompt: two-sentence story openings, 8 genres rotated evenly, unique mundane-theme perturbation per prompt, temperature 1.0, max_tokens 80.

Samples per model: `anthropic/claude-sonnet-4.5` = 200, `deepseek/deepseek-v3.1-terminus` = 200, `google/gemini-2.5-flash` = 200, `meta-llama/llama-4-maverick` = 200, `openai/gpt-5-mini` = 200

Baselines: SSA baby names 1950–2020 (first names), US Census 2010 (surnames), both add-one smoothed. `lift = llm_freq / human_freq`. Blocklist: name in ≥2 samples for ≥2 models and lift ≥ 50.0×.

## Data quality
**Blocklist coverage.** Sample-level presence of *any* final-blocklist name (first or surname, real+invented) in a completion: **763/1000 = 76.3%**. Restricting to real-tier names only: 758/1000 = 75.8%. (This is the '~76%' headline; a name counts once per sample regardless of repeats.)

**Truncation.** `max_tokens=80`, so many completions stop mid-sentence (no terminal punctuation). Likely-truncated samples per model:
| model | truncated / total | % |
|---|---|---|
| claude-sonnet-4.5 | 127 / 200 | 64% |
| deepseek-v3.1-terminus | 18 / 200 | 9% |
| gemini-2.5-flash | 51 / 200 | 26% |
| llama-4-maverick | 193 / 200 | 96% |
| gpt-5-mini | 188 / 200 | 94% |

Truncation does **not** overturn the role analysis: ≥2 characters are named in 93% of samples, and the secondary character is 33% female in truncated samples vs 38% in complete ones — the male-secondary skew holds in both.

## Blocklist
31 first names, 15 surnames (40 real names, 6 invented).

Two tiers are reported separately because lift means different things for each. **Real names** exist in the human baseline, so their lift is a genuine over-use ratio. **Invented names** have no baseline at all, so their lift is just the add-one floor (identical millions-× values on a handful of hits) — they are ranked by frequency, not lift.

### Tier 1 — real names, ranked by lift (the useful list)
Names marked † have fewer than 10 pooled hits — thin evidence; treat the lift as indicative, not precise (see the wide CI).

| name | type | pooled n | lift | lift 95% CI | models | genres | SSA/Census n |
|---|---|---|---|---|---|---|---|
| Elara | first | 153 | 48772× | 42084–56307× | 5 | 8 | 815 |
| Eira | first | 15 | 8197× | 4979–13444× | 2 | 1 | 475 |
| Kaelen | first | 30 | 7681× | 5400–10882× | 2 | 3 | 1015 |
| Thorne† | first | 8 | 5125× | 2601–10063× | 2 | 1 | 405 |
| Hawk† | first | 7 | 2268× | 1100–4658× | 2 | 3 | 802 |
| Kael | first | 22 | 1660× | 1099–2496× | 5 | 2 | 3447 |
| Lyra | first | 26 | 1440× | 986–2095× | 4 | 2 | 4696 |
| Arin | first | 13 | 780× | 456–1326× | 2 | 2 | 4337 |
| Blackwood | surname | 17 | 597× | 374–950× | 2 | 7 | 8407 |
| Kaelin† | first | 8 | 581× | 295–1140× | 2 | 1 | 3583 |
| Windsor | surname | 12 | 465× | 266–808× | 2 | 4 | 7621 |
| Emilia | first | 57 | 361× | 280–463× | 2 | 7 | 41120 |
| Lena | first | 41 | 252× | 186–338× | 4 | 6 | 42389 |
| Mayfield | surname | 24 | 238× | 160–351× | 2 | 4 | 29805 |
| Thorne | surname | 15 | 236× | 143–387× | 4 | 5 | 18738 |
| Wellington† | surname | 5 | 217× | 93–507× | 2 | 4 | 6784 |
| Leo | first | 85 | 212× | 173–260× | 2 | 7 | 104138 |
| Finnley† | first | 4 | 195× | 76–498× | 2 | 3 | 5346 |
| Grey† | surname | 8 | 186× | 94–366× | 2 | 3 | 12680 |
| Finn | first | 16 | 163× | 100–263× | 3 | 6 | 25581 |
| Jax | first | 12 | 162× | 93–282× | 3 | 1 | 19256 |
| Maya | first | 57 | 144× | 112–184× | 5 | 6 | 103229 |
| Chen | surname | 80 | 139× | 113–171× | 3 | 7 | 169580 |
| Mara | first | 11 | 138× | 77–245× | 2 | 5 | 20786 |
| Clara | first | 36 | 126× | 91–172× | 3 | 5 | 74604 |
| Gable† | surname | 4 | 121× | 47–309× | 2 | 2 | 9779 |
| Anya† | first | 7 | 107× | 52–220× | 2 | 4 | 17004 |
| Matt† | first | 8 | 105× | 53–206× | 2 | 2 | 19864 |
| Zara† | first | 5 | 96× | 41–223× | 3 | 3 | 13608 |
| Patel | surname | 70 | 90× | 72–112× | 3 | 6 | 229973 |
| Marcus | first | 72 | 84× | 67–104× | 5 | 7 | 223659 |
| Jasper | first | 11 | 80× | 45–143× | 3 | 5 | 35614 |
| Elias | first | 26 | 78× | 54–114× | 2 | 7 | 86197 |
| Arthur | first | 45 | 65× | 49–86× | 2 | 7 | 180263 |
| Liam | first | 63 | 65× | 51–82× | 4 | 8 | 253439 |
| Ben† | first | 9 | 63× | 33–119× | 3 | 4 | 37349 |
| Vance | surname | 10 | 62× | 34–114× | 2 | 3 | 47324 |
| Eleanor | first | 20 | 61× | 40–94× | 3 | 6 | 85038 |
| Elena | first | 18 | 60× | 38–95× | 4 | 6 | 77711 |
| Maynard† | surname | 7 | 57× | 27–116× | 2 | 2 | 36460 |

### Tier 2 — invented names, ranked by frequency
(All invented names are low-count and genre-specific — treat as the least reliable part of the list.)

| name | type | pooled n | models | top genre |
|---|---|---|---|---|
| Elianore | first | 13 | 2 | science fiction |
| Quasar | surname | 13 | 2 | science fiction |
| Shadowglow | surname | 13 | 2 | high fantasy |
| Vex | surname | 13 | 2 | science fiction |
| Lyrien† | first | 5 | 2 | high fantasy |
| Fanshawe† | surname | 4 | 2 | historical fiction |

## Per-model top 20 names (by sample count)

### anthropic/claude-sonnet-4.5

| name | type | n | share of 200 | lift |
|---|---|---|---|---|
| Marcus | first | 65 | 32% | 84× |
| Chen | surname | 64 | 32% | 139× |
| Sarah | first | 27 | 14% | 14× |
| Maya | first | 19 | 10% | 144× |
| Webb | surname | 15 | 8% | 26× |
| Elena | first | 14 | 7% | 60× |
| James | first | 13 | 6% | 3× |
| Mira | first | 13 | 6% | 363× |
| Margaret | first | 10 | 5% | 8× |
| Mara | first | 9 | 4% | 138× |
| Margot | first | 9 | 4% | 186× |
| Kael | first | 7 | 4% | 1660× |
| Priya | first | 6 | 3% | 261× |
| Chen | first | 6 | 3% | 6476× |
| Dev | first | 5 | 2% | 509× |
| Yara | first | 5 | 2% | 262× |
| Marina | first | 5 | 2% | 38× |
| David | first | 4 | 2% | 0× |
| Thomas | first | 4 | 2% | 4× |
| Diane | first | 4 | 2% | 3× |

### deepseek/deepseek-v3.1-terminus

| name | type | n | share of 200 | lift |
|---|---|---|---|---|
| Leo | first | 60 | 30% | 212× |
| Arthur | first | 39 | 20% | 65× |
| Elara | first | 38 | 19% | 48772× |
| Clara | first | 30 | 15% | 126× |
| Kaelen | first | 26 | 13% | 7681× |
| Liam | first | 26 | 13% | 65× |
| Maya | first | 17 | 8% | 144× |
| Lena | first | 17 | 8% | 252× |
| Elias | first | 16 | 8% | 78× |
| Thorne | surname | 10 | 5% | 236× |
| Aris | first | 10 | 5% | 755× |
| Vance | surname | 7 | 4% | 62× |
| Finch | surname | 6 | 3% | 67× |
| Chloe | first | 6 | 3% | 13× |
| Kael | first | 5 | 2% | 1660× |
| Eleanor | first | 5 | 2% | 61× |
| Ben | first | 5 | 2% | 63× |
| Amelia | first | 5 | 2% | 22× |
| Rostova | surname | 5 | 2% | 1770849× |
| Lyra | first | 4 | 2% | 1440× |

### google/gemini-2.5-flash

| name | type | n | share of 200 | lift |
|---|---|---|---|---|
| Elara | first | 92 | 46% | 48772× |
| Liam | first | 25 | 12% | 65× |
| Leo | first | 25 | 12% | 212× |
| Sarah | first | 15 | 8% | 14× |
| Eleanor | first | 14 | 7% | 61× |
| Thomas | first | 12 | 6% | 4× |
| Finn | first | 12 | 6% | 163× |
| Elias | first | 10 | 5% | 78× |
| Amelia | first | 10 | 5% | 22× |
| Jax | first | 9 | 4% | 162× |
| Maya | first | 8 | 4% | 144× |
| Mark | first | 8 | 4% | 2× |
| Arthur | first | 6 | 3% | 65× |
| Chloe | first | 5 | 2% | 13× |
| Beatrice | first | 5 | 2% | 47× |
| Kael | first | 4 | 2% | 1660× |
| Clara | first | 4 | 2% | 126× |
| Kaelen | first | 4 | 2% | 7681× |
| Anya | first | 4 | 2% | 107× |
| Miles | first | 4 | 2% | 16× |

### meta-llama/llama-4-maverick

| name | type | n | share of 200 | lift |
|---|---|---|---|---|
| Emily | first | 81 | 40% | 47× |
| Rachel | first | 58 | 29% | 49× |
| Patel | surname | 39 | 20% | 90× |
| Emilia | first | 37 | 18% | 361× |
| Wilson | surname | 29 | 14% | 17× |
| Lee | surname | 18 | 9% | 9× |
| Mayfield | surname | 18 | 9% | 238× |
| Taylor | surname | 13 | 6% | 11× |
| Thompson | surname | 13 | 6% | 7× |
| Eira | first | 12 | 6% | 8197× |
| Olivia | first | 11 | 6% | 9× |
| Arin | first | 11 | 6% | 780× |
| Sophia | first | 11 | 6% | 17× |
| Blackwood | surname | 11 | 6% | 597× |
| Maya | first | 10 | 5% | 144× |
| Lena | first | 10 | 5% | 252× |
| Shadowglow | surname | 10 | 5% | 3836839× |
| Lyra | first | 9 | 4% | 1440× |
| Jenkins | surname | 9 | 4% | 25× |
| Elianore | first | 9 | 4% | 3381514× |

### openai/gpt-5-mini

| name | type | n | share of 200 | lift |
|---|---|---|---|---|
| Emily | first | 60 | 30% | 47× |
| Rachel | first | 37 | 18% | 49× |
| Patel | surname | 29 | 14% | 90× |
| Emilia | first | 20 | 10% | 361× |
| Emma | first | 19 | 10% | 12× |
| Wilson | surname | 18 | 9% | 17× |
| Taylor | surname | 15 | 8% | 11× |
| Elara | first | 12 | 6% | 48772× |
| Lena | first | 12 | 6% | 252× |
| Sophia | first | 12 | 6% | 17× |
| Lyra | first | 10 | 5% | 1440× |
| Chen | surname | 9 | 4% | 139× |
| Jenkins | surname | 9 | 4% | 25× |
| Alex | first | 9 | 4% | 9× |
| James | first | 8 | 4% | 3× |
| Jack | first | 8 | 4% | 12× |
| Windsor | surname | 8 | 4% | 465× |
| Jamie | first | 7 | 4% | 8× |
| Vex | surname | 7 | 4% | 3836839× |
| Lucy | first | 7 | 4% | 18× |

## Names every model loves
Appearing ≥2× in **all** 5 models:

| name | type | pooled n | lift |
|---|---|---|---|
| Elara | first | 153 | 48772× |
| Maya | first | 57 | 144× |
| Kael | first | 22 | 1660× |

## Gender
First-name mentions classified via SSA sex ratio (≥80% one sex = gendered; the middle band is ambiguous). Counts are sample-level presence.

| model | total mentions | female / male | % female | distinct ♀ names | top ♀ name | top ♀ share | Elara ♀ share |
|---|---|---|---|---|---|---|---|
| claude-sonnet-4.5 | 441 | 213 / 168 | 56% | 80 | Sarah (27) | 13% | 1% |
| deepseek-v3.1-terminus | 417 | 168 / 192 | 47% | 46 | Elara (38) | 23% | 23% |
| gemini-2.5-flash | 394 | 201 / 179 | 53% | 45 | Elara (92) | 46% | 46% |
| llama-4-maverick | 454 | 289 / 118 | 71% | 42 | Emily (81) | 28% | 3% |
| gpt-5-mini | 462 | 265 / 137 | 66% | 67 | Emily (60) | 23% | 4% |

**Distribution collapse:** `top ♀ share` is the fraction of a model's female protagonists carried by its single most common female name. Gemini's Elara alone accounts for ~46% of its female characters — 3× the concentration of any other model — while Claude's female names are the most varied.

- **claude-sonnet-4.5** — top ♀: Sarah 27, Maya 19, Elena 14, Mira 13, Margaret 10, Mara 9
- **deepseek-v3.1-terminus** — top ♀: Elara 38, Clara 30, Lena 17, Maya 17, Chloe 6, Eleanor 5
- **gemini-2.5-flash** — top ♀: Elara 92, Sarah 15, Eleanor 14, Amelia 10, Maya 8, Chloe 5
- **llama-4-maverick** — top ♀: Emily 81, Rachel 58, Emilia 37, Eira 12, Sophia 11, Olivia 11
- **gpt-5-mini** — top ♀: Emily 60, Rachel 37, Emilia 20, Emma 19, Sophia 12, Lena 12

## Protagonist vs secondary character
The prompt asks for a protagonist then one secondary character, so the first-named person is the protagonist and the second is the secondary. Splitting by role reveals a strong structural default that the pooled gender balance hides.

**Pooled:** protagonists are 76% female; secondary characters are 35% female (65% male). The models overwhelmingly default to a female lead paired with a male supporting character.

| model | protagonist % female | secondary % female |
|---|---|---|
| claude-sonnet-4.5 | 75% | 42% |
| deepseek-v3.1-terminus | 38% | 47% |
| gemini-2.5-flash | 76% | 24% |
| llama-4-maverick | 93% | 33% |
| gpt-5-mini | 91% | 32% |

Most common protagonist / secondary gender pairing (pooled):

| pairing | share |
|---|---|
| female primary + male secondary | 57% |
| female primary + female secondary | 18% |
| male primary + female secondary | 16% |
| male primary + male secondary | 10% |

Top protagonist names vs top secondary names (pooled):

- **protagonists:** Elara 130, Emily 128, Emilia 52, Maya 46, Leo 35, Arthur 33, Sarah 32, Marcus 28
- **secondary:** Chen 55, Wilson 47, Leo 44, Liam 37, Rachel 29, Taylor 25, Clara 23, Thorne 20

## Cross-check vs prior work (the ghost couple)
Presence of the character clusters reported by Brzozowski & Chung (arXiv:2606.02184) in our fiction samples (raw full-name match):

| name | their attribution | total hits | our hits by model |
|---|---|---|---|
| Elena Vasquez | claude (theirs) | 3 | claude-sonnet-4.5:3 |
| Marcus Chen | claude (theirs) | 9 | claude-sonnet-4.5:9 |
| Amara Okafor | claude (theirs) | 0 | — |
| Aris Thorne | gemini (theirs) | 6 | deepseek-v3.1-terminus:6 |
| Lena Petrova | gemini (theirs) | 2 | deepseek-v3.1-terminus:1, gemini-2.5-flash:1 |
| Elara Voss | gpt (theirs) | 0 | — |

**Ensemble test (Marcus + Chen, Claude):** Marcus in 65/200 stories, Chen in 70, both in **38** (chance would give ~22.7) — a co-occurrence lift of 1.67×. Real but modest; the 'couple' is looser in fiction than in fabricated-expert text.

## Genre conditioning
Blocklist names with ≥60% of hits in a single genre:

| name | genre | share | pooled n |
|---|---|---|---|
| Eira | high fantasy | 100% | 15 |
| Kaelen | high fantasy | 63% | 30 |
| Thorne | high fantasy | 100% | 8 |
| Hawk | thriller | 71% | 7 |
| Kael | high fantasy | 77% | 22 |
| Lyra | high fantasy | 85% | 26 |
| Arin | high fantasy | 85% | 13 |
| Kaelin | high fantasy | 100% | 8 |
| Jax | science fiction | 100% | 12 |
| Gable | horror | 75% | 4 |
| Matt | horror | 88% | 8 |
| Maynard | contemporary story set in the UK | 71% | 7 |
| Elianore | science fiction | 92% | 13 |
| Quasar | science fiction | 92% | 13 |
| Shadowglow | high fantasy | 100% | 13 |
| Vex | science fiction | 77% | 13 |
| Lyrien | high fantasy | 100% | 5 |
| Fanshawe | historical fiction | 100% | 4 |
