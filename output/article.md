# Everyone's Name Is Elara Now: Measuring Character-Name Slop in Five LLMs

*Draft — July 2026. Data and code: this repository.*

Ask a large language model to write you the opening of a short story and there's
a decent chance the hero will be called Elara. Ask five different models, a
thousand times, and you stop guessing and start counting. We did. **In 76% of a
thousand story openings (763 of 1,000), the model reached for a name from a
small, predictable pool** — the same two or three dozen names, over and over,
regardless of which lab built the model. (That 76% is the share of completions
containing at least one name from our final blocklist — first or surname,
counted once per story; see Data quality in the report for the exact figures.)

This is the phenomenon writers have started calling *slop*: not wrong, exactly,
but flat, over-smoothed, unmistakably machine-made. Names are the purest example
because a name carries no plot and hides no reasoning — it's a naked draw from
the model's distribution. If that distribution has collapsed onto "Elara" and
"Kael" and "Marcus Chen," you can see it in a single word.

## Prior work: the ghost couple

This behaviour is not something we discovered from scratch. In *"The Ghost
Couple: Correlated LLM Name Priors and Their Haunting of the Web and Academic
Publishing"* (Brzozowski & Chung, [arXiv:2606.02184](https://arxiv.org/abs/2606.02184),
June 2026), the authors show that models don't merely default to
high-probability individual names — they emit *correlated character ensembles*,
pairs and trios whose co-occurrence beats chance and recur across independent
generations. They report the fingerprints by model family (Claude: Elena
Vasquez + Marcus Chen + Amara Okafor; Gemini: Aris Thorne + Lena Petrova; GPT:
Elara Voss), find them version-specific and suppressed at release boundaries,
and trace real downstream harm — thousands of "ghost-authored" records on
Zenodo naming these nonexistent people.

Our contribution is not the phenomenon but a different cut of it: we measure it
in **creative fiction** rather than fabricated experts, quantify over-use as
**lift against human-name baselines** (SSA and Census) rather than raw
co-occurrence, add **genre, narrative-role, and gender** analysis, and ship a
**writer-facing blocklist**. And because we sampled current models in a
different domain, our data serves as an independent check on their fingerprints
— which it both confirms and complicates (see "Cross-checking the ghost couple"
below).

## Why a blocklist

If you write fiction with these tools, or build products on top of them, the
overused names are a tax on originality. They make first drafts feel
interchangeable, they give away that a passage was generated, and they crowd out
the long tail of perfectly good names the model *could* have used. A blocklist —
a list of names to steer away from — is a cheap fix: drop it into a system
prompt, a sampler, or an editing pass and you buy back some variety for free.

But "names LLMs use a lot" is not quite the right target. Models use "James" and
"Sarah" a lot too, and so do humans — banning them would be silly. What you want
are names that are **over**used: far more common in machine text than in the
actual population of human names. That's a ratio, and measuring it is the whole
game.

## How we measured it

We prompted five models — one per major lab — through fal's `any-llm` endpoint:

- OpenAI **GPT-5-mini**
- Google **Gemini 2.5 Flash**
- Anthropic **Claude Sonnet 4.5**
- Meta **Llama 4 Maverick**
- DeepSeek **v3.1 Terminus**

Each model got 200 prompts of the form *"Write the opening two sentences of a
{genre} short story involving {a mundane object}. Introduce the protagonist and
one secondary character by name."* We rotated evenly through eight genres (high
fantasy, sci-fi, literary, romance, thriller, historical, horror, and
UK-contemporary) and appended a different everyday noun to every prompt — a
lighthouse, a missed train, a jar of honey — so that no two prompts were
identical and providers couldn't serve us a cached response. Temperature was
held at 1.0: we wanted the model's distribution, not its single most likely
answer.

From each completion we pulled person names with spaCy's named-entity
recogniser (plus a fallback for messier output), split them into first names and
surnames, and counted how many *samples* each name appeared in. Then, for every
name, we computed **lift**:

> lift = (share of LLM samples containing the name) ÷ (share of the name in a
> human baseline)

The human baseline is US Social Security first-name data (1950–2020) and US
Census 2010 surnames, add-one smoothed so that a name absent from the baseline
doesn't divide by zero. A lift of 100× means the models use the name a hundred
times more often than its human prevalence would predict.

A name makes the blocklist if it appears in at least two samples for at least
two different models and clears a lift threshold of 50×. That "two models" rule
matters: it throws out any one model's private tics and keeps only slop that
generalises.

## The one honest caveat, up front

Raw lift has a trap in it, and it's worth naming before showing any rankings. A
name the models *invented* — "Elianore," "Shadowglow," "Quasar" — has a human
baseline of exactly zero. After smoothing, its lift comes out in the millions,
purely because we're dividing by the noise floor. Sorted naively, the top of the
list is all fantasy confections, and you'd conclude that LLM name-slop is a
fantasy problem.

It isn't. Those invented names are *rare* in our samples (four to thirteen hits
each) and, being invented, they only ever show up in fantasy and sci-fi — the
two genres where a model feels licensed to make things up. Their sky-high lift
is an artefact of the metric, not evidence of overuse.

So we split the blocklist into two tiers:

- **Tier 1 — real names** that exist in the human data. For these, lift is a
  true over-use ratio, and it's the list you actually want.
- **Tier 2 — invented names** with no baseline. We report them for interest but
  rank them by frequency, since their lift is meaningless.

Everything below is Tier 1 unless stated.

## Result 1: Elara is the queen, but she has a favourite model

"Elara" appears in **153 of 1,000 openings (15.3%)** — she is, by a wide margin,
the single most overused character name in the study, with a lift of roughly
49,000×. She is the only name to clear the bar in all five models. But the
per-model breakdown is the surprise:

| Model | Elara's share of its stories |
|---|---|
| Google Gemini 2.5 Flash | **46%** |
| DeepSeek v3.1 | 19% |
| OpenAI GPT-5-mini | 6% |
| Meta Llama 4 Maverick | 4% |
| Anthropic Claude Sonnet 4.5 | **2%** |

Nearly half of Gemini's protagonists are named Elara. Claude almost never uses
the name. "Universal slop" turns out to be universal in *reach* but wildly
uneven in *degree* — which is exactly why pooling across labs matters.

## Result 2: the effect is really a collapse of the *female* name distribution

Look only at the names a model gives its female characters and the Elara effect
sharpens into something more diagnostic. We classified every first name by its
SSA sex ratio (a name is "female" if ≥80% of its US registrations are female)
and asked, per model, what share of its female protagonists carry its single
most-used female name:

| Model | Top female name | Its share of *all* female characters | Distinct female names |
|---|---|---|---|
| Google Gemini 2.5 Flash | **Elara** | **46%** | 45 |
| Meta Llama 4 Maverick | Emily | 28% | 42 |
| DeepSeek v3.1 | Elara | 23% | 46 |
| OpenAI GPT-5-mini | Emily | 23% | 67 |
| Anthropic Claude Sonnet 4.5 | Sarah | 13% | 80 |

This is the real shape of the problem. **Almost one in every two female
characters Gemini invents is named Elara** — three times the concentration of
any other model's favourite, and drawn from a visibly narrower pool (45 distinct
female names against Claude's 80). Claude, at the other extreme, spreads its
women across the widest set of names and leans on its top pick only an eighth of
the time.

The collapse isn't unique to Gemini or to women, either — it just moves. On the
*male* side, Claude shows the same pathology in mirror image: **41% of its male
characters are named Marcus.** Each model has a name it can't stop reaching for;
the gender lens just reveals which slot has collapsed.

## Result 3: a female lead and her male sidekick

Because each prompt asks for a protagonist *and* a secondary character, we can
split every name by narrative role — the first-named person is the lead, the
second is support — and the structural default is striking:

| Role | Share female (pooled) |
|---|---|
| Protagonist | **75%** |
| Secondary character | **35%** (i.e. 65% male) |

The models overwhelmingly write **a woman as the hero and a man beside her.**
The single most common gender template, across all five models and all 1,000
stories, is *female lead + male secondary* (57% of stories); *male lead + male
secondary* is the rarest (10%). This also explains the earlier puzzle of why
Gemini looked gender-balanced overall (53% female): that balance is an artefact
of averaging a 76%-female protagonist slot against a 24%-female secondary slot.
The roles are strongly gendered in opposite directions; the average just hides
it.

Per model, the lead-is-female default ranges from near-absolute to inverted:

| Model | Protagonist % female | Secondary % female |
|---|---|---|
| Llama 4 Maverick | 93% | 33% |
| GPT-5-mini | 91% | 32% |
| Gemini 2.5 Flash | 76% | 24% |
| Claude Sonnet 4.5 | 75% | 42% |
| DeepSeek v3.1 | 38% | 47% |

DeepSeek is the lone dissenter — it prefers a male lead (Leo, Arthur), which is
of a piece with its generally antiquarian taste. And the name pools differ by
role, not just gender: protagonists are Elara, Emily, Maya; secondary characters
are disproportionately known by *surname* — Chen, Wilson, Taylor, Thorne — the
"and her colleague, Detective Chen" slot.

## Result 4: every lab has an accent

Read the per-model top lists side by side and the models sort into distinct
dialects:

- **Claude Sonnet 4.5 — corporate-realist.** Its leads are contemporary
  professionals: Marcus is Claude's default (male) protagonist, and its most
  common *secondary* character is someone surnamed **Chen** — usually a separate
  person ("Marcus… and his colleague Chen"), not one "Marcus Chen" (that exact
  pairing appears in only 9 of 200 stories). Claude's imagination runs to
  offices, not elves.
- **Gemini 2.5 Flash — the Elara machine**, as above.
- **DeepSeek v3.1 — the antiquarian.** Leo (29%), Arthur (20%), Clara (14%),
  Eleanor — a cast that sounds like a 1920s boarding school, leavened with
  fantasy (Kaelen, 12%).
- **Llama 4 Maverick and GPT-5-mini — near-twins.** Both open, in order, with
  Emily, Rachel, and the surname **Patel**, then Emilia and Wilson. Their
  top-tens are strikingly similar — we can't say why from this data alone (shared
  training sources and shared RLHF conventions are both plausible), only that the
  overlap is unusually high. Llama alone also freely mints fantasy surnames
  (Shadowglow, Quasar).

The heatmap (`heatmap.html`) makes these accents visible at a glance: dark rows
are names one model loves and the others ignore.

## Result 5: the useful slop is *not* genre-bound

Having removed the invented names, is the real-name list still fantasy-heavy? No.
The genuinely overused names spread across genres:

- **Elara** appears in all **8** genres.
- **Marcus, Chen, Leo, Emilia, Elias, Arthur, Liam** each span **7–8** genres.
- **Maya, Lena, Clara, Elena, Eleanor, Finn** span **6**.

The fantasy lock-in is real but confined to a specific cluster: **Kael, Kaelen,
Kaelin, Lyra, Arin, Eira, Jax** are 80–100% fantasy or sci-fi. Those are worth a
separate genre-specific blocklist. The cross-genre names above are the ones that
will out a generated passage no matter what you asked for.

## Result 6: the phonetics of a machine name

The real-name list has an audible shape. Of 28 overused first names, **11 end in
"-a"** (Elara, Eira, Lyra, Emilia, Lena, Maya, Mara, Clara, Anya, Zara, Elena)
and a full cluster begins with **"El-"** (Elara, Elias, Eleanor, Elena) or the
fantasy **"Kae-"** stem (Kael, Kaelen, Kaelin). Soft consonants, open vowels,
two or three syllables, faintly antique or faintly elvish. Models have converged
on a single aesthetic for "this sounds like a protagonist," and it is vowel-heavy
and gently mythic.

## Result 7: Thorne is so overused it works at both ends of a name

The best single artefact in the data: **"Thorne" appears as both a first name and
a surname.** As a surname it's the brooding "Aris Thorne," "Elias Thorne,"
"Magister Thorne." As a first name it's almost always **"Thorne Blackwood"** — a
character built by welding two blocklisted surnames together. When a model needs a
name to sound gothic, "Thorne" is so load-bearing it will deploy it wherever a
name slot opens.

## Result 8: cross-checking the ghost couple

Because Brzozowski & Chung name specific clusters, we can test their fingerprints
against our (independently generated, fiction-domain) samples. The result is a
partial replication — which is exactly what you'd hope for from an independent
measurement:

| Their reported cluster | In our 1,000 fiction samples |
|---|---|
| Claude: **Elena Vasquez** | 3 hits — all Claude ✓ |
| Claude: **Marcus Chen** | 9 hits — all Claude ✓ |
| Gemini: Aris Thorne | 6 hits — all **DeepSeek**, not Gemini |
| Gemini: Lena Petrova | 2 hits (1 DeepSeek, 1 Gemini) |
| GPT: Elara Voss | 0 — our Elara is bare "Elara", and it's **Gemini's** |
| Claude: Amara Okafor | 0 |

The Claude fingerprint replicates cleanly: the exact surnames they flag (Vasquez,
Chen) show up only in Claude here too. But the attributions **move across
domains**. They tie Elara to GPT; in fiction it's overwhelmingly Gemini's (46%
of its stories). They tie Aris Thorne to Gemini; we see it only in DeepSeek. Far
from undermining either result, this pins down what kind of thing a name prior
is: **domain-specific and version-specific**, not a fixed property of a model.
The fingerprint is real; the ink changes with the surface.

We can also test their central claim directly — that these are *ensembles*, not
independent names. In our Claude samples, "Marcus" appears in 65 stories and
"Chen" in 70; if they were independent they'd co-occur in ~23 stories by chance,
but they actually share **38** — a co-occurrence lift of 1.7×. So the pairing is
real but, in fiction, looser than the "couple" metaphor implies. The tightest
recurring duo we found is Llama's **Emily + Rachel** (together in 39 of 200
stories), and Gemini's Elara behaves like their partnerless "Elara Voss" — a hub
that pairs with a rotating cast of male secondaries (Elara + Liam, Elara + Finn,
Elara + Leo) rather than one fixed companion.

## The blocklist

The full ranked lists live in `blocklist.json` (structured for dropping into
other tools) and `name_counts.csv` (every name with per-model counts). The
headline entries:

**Most overused real first names** (by lift): Elara, Eira, Kaelen, Thorne, Hawk,
Kael, Lyra, Arin, Kaelin, Emilia, Lena, Leo, Maya, Mara, Clara, Marcus, Elias,
Arthur, Liam, Eleanor, Elena.

**Most overused surnames**: Blackwood, Windsor, Mayfield, Thorne, Wellington,
Grey, Chen, Patel, Vance, Maynard.

**Invented confections** (use-at-your-own-risk, fantasy/sci-fi only, all
low-count): Elianore, Lyrien, Quasar, Shadowglow, Vex, Fanshawe.

## Limitations

This is a measurement, not a verdict, and a few caveats deserve to be as loud as
the findings:

- **Completions were truncated.** We capped generation at 80 tokens to keep
  costs down, so many completions stop mid-sentence — heavily so for some models
  (Llama 96%, GPT-5-mini 94%, Claude 64%; Gemini and DeepSeek much less). This
  matters most for the protagonist/secondary split, since a cut-off story might
  never reach its second character. We checked: both characters are still named
  in 93% of samples (they arrive in the first sentence or two), and the
  male-secondary skew holds in both truncated and complete subsets (33% vs 38%
  female secondary). So the effect survives, but a longer cap would measure it
  more cleanly.
- **The role/gender finding may be partly prompt-shaped.** The prompt names "the
  protagonist and one secondary character," which could itself nudge the model
  toward "female lead + male colleague/friend." We have not yet run the neutral
  controls ("introduce two named characters," or role-reversed prompts) needed to
  separate a genuine model prior from prompt suggestion. Treat the *direction* as
  real and the *magnitude* as provisional until that robustness set is run.
- **Extraction is imperfect.** spaCy's small NER model misses and mislabels;
  we patch the common cases (possessives, "the Wilsons," place/building spans
  like "Ravenswood Lighthouse," role-titles like "DJ", kinship titles, a
  name-gazetteer rescue), but the long tail still has noise, and it lands
  hardest on low-count and invented names — exactly the least reliable rows.
- **Low-count names are thin evidence.** Names with fewer than 10 hits are
  flagged † in the report and carry a `unstable` flag plus a 95% Wilson
  confidence interval in `blocklist.json` / `name_counts.csv`. For a name seen 4
  times, the CI on its lift spans a factor of several — real signal, imprecise
  number.
- **The baseline is US-centric.** SSA and Census data under-count names common
  elsewhere; "Patel" is enormous in the real world but its US-Census share still
  leaves it looking over-used here. Read surname lift with that grain of salt.
- **Lift rewards rarity**, which is why we tiered the list. Even within Tier 1,
  a rare-but-real name (Elara) will out-lift a common one (Marcus) that the model
  arguably leans on just as hard in absolute terms.
- **Five models, one prompt shape, 200 samples each.** Different genres, prompt
  phrasings, or temperatures would shift the numbers. The *direction* — heavy
  concentration on a small pool — is robust; the exact ranks are not gospel.

## Using it

Drop `blocklist.json` into a system prompt ("avoid these overused names:
…"), a logit bias, or a post-generation lint. Re-running `python run.py analyze`
is free and recomputes everything from the saved samples, so you can retune the
lift threshold or add a baseline without spending another token. To refresh the
underlying data as models change, `python run.py sample` re-samples from scratch.

The point isn't that Elara is a bad name. It's that she shouldn't be *every*
name — and now there's a number for how often she is.

## References

- Michał Brzozowski and Neo Christopher Chung. *The Ghost Couple: Correlated LLM
  Name Priors and Their Haunting of the Web and Academic Publishing.* arXiv:2606.02184,
  June 2026. <https://arxiv.org/abs/2606.02184>
- US Social Security Administration, national baby-name data (first-name
  baseline). US Census Bureau, 2010 surname frequencies (surname baseline).
