"""Configuration for the LLM character-name slop blocklist project."""

# --- FAL any-llm ---------------------------------------------------------
FAL_ENDPOINT = "https://fal.run/fal-ai/any-llm"

# One model per lab, all valid enum values on fal-ai/any-llm (checked 2026-07-06).
MODELS = [
    "openai/gpt-5-mini",
    "google/gemini-2.5-flash",
    "anthropic/claude-sonnet-4.5",
    "meta-llama/llama-4-maverick",
    "deepseek/deepseek-v3.1-terminus",
]

# --- Sampling ------------------------------------------------------------
SAMPLES_PER_MODEL = 200
MAX_TOKENS = 80          # hard cap per completion
TEMPERATURE = 1.0        # never below 0.8; dropped entirely if the provider rejects it
MAX_TOTAL_CALLS = 2000   # abort with confirmation prompt above this
RANDOM_SEED = 20260706   # reproducible prompt schedule

# {genre_phrase} is "<genre> short story", or the genre verbatim if it
# already contains the word "story" (e.g. "contemporary story set in the UK").
PROMPT_TEMPLATE = (
    "Write the opening two sentences of a {genre_phrase}{theme_clause}. "
    "Introduce the protagonist and one secondary character by name."
)

# Robustness variants for testing whether the female-lead/male-secondary
# finding is prompt-elicited. `default` mirrors PROMPT_TEMPLATE; `neutral`
# removes role labels; `reversed_roles` flips the naming order. Select with
# `--variant`; variant runs write to output/samples_<variant>/ so they never
# mix with the main dataset.
PROMPT_VARIANTS = {
    "default": PROMPT_TEMPLATE,
    "neutral": (
        "Write the opening two sentences of a {genre_phrase}{theme_clause}. "
        "Introduce two named characters."
    ),
    "reversed_roles": (
        "Write the opening two sentences of a {genre_phrase}{theme_clause}. "
        "Introduce a secondary character and the protagonist by name."
    ),
}

GENRES = [
    "high fantasy",
    "science fiction",
    "contemporary literary fiction",
    "romance",
    "thriller",
    "historical fiction",
    "horror",
    "contemporary story set in the UK",
]

# Mundane theme nouns; one is appended to every prompt so no two prompts are
# identical, which defeats provider-side response caching.
THEMES = [
    "a lighthouse", "a missed train", "a borrowed umbrella", "a broken clock",
    "a jar of honey", "a secondhand bicycle", "an unpaid bill", "a lost glove",
    "a garden shed", "a pot of coffee", "a stray dog", "a ferry ticket",
    "a crossword puzzle", "a tin of spilled paint", "an antique mirror",
    "an empty suitcase", "a letter sent to the wrong address", "a dripping tap",
    "a library card", "a chess set", "a bag of oranges", "a locked drawer",
    "a late-night radio broadcast", "a paper map", "a wool scarf",
    "a night bus", "a hotel key", "a postage stamp", "a folding chair",
    "an old kettle",
]

# --- Analysis ------------------------------------------------------------
# SSA counts are aggregated over this inclusive year range (people alive today
# who could plausibly be adult fiction protagonists). Mirror data ends 2020.
SSA_YEAR_RANGE = (1950, 2020)
SSA_URL = "https://www.ssa.gov/oact/babynames/names.zip"
# ssa.gov 403s non-browser clients (Akamai); this GitHub mirror of the same
# names.zip (yob1880-yob2020) is used as fallback.
SSA_MIRROR_URL = ("https://raw.githubusercontent.com/hackerb9/ssa-baby-names/"
                  "master/raw-data/names.zip")
# US Census 2010 surname frequencies, used as the surname baseline.
CENSUS_SURNAMES_URL = "https://www2.census.gov/topics/genealogy/2010surnames/names.zip"

LIFT_THRESHOLD = 50.0    # pooled lift must exceed this to enter the blocklist
MIN_SAMPLES = 2          # name must appear in >= this many samples ...
MIN_MODELS = 2           # ... for >= this many distinct models

# --- Paths ---------------------------------------------------------------
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
SAMPLES_DIR = os.path.join(OUTPUT_DIR, "samples")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
