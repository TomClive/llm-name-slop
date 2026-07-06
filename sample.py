"""Sampling: build the prompt schedule and collect completions to JSONL."""

import datetime
import json
import os
import random
import sys

import config
import falclient


def build_schedule(n_samples: int, seed: int,
                   template: str = config.PROMPT_TEMPLATE) -> list[dict]:
    """Deterministic schedule of n_samples (genre, theme) prompts.

    Genres rotate evenly; themes are drawn without replacement within each
    genre so every prompt string in a run is unique (8 genres x 30 themes =
    240 unique prompts, enough for 200 samples with even genre coverage).
    """
    rng = random.Random(seed)
    per_genre = -(-n_samples // len(config.GENRES))  # ceil
    if per_genre > len(config.THEMES):
        raise ValueError(
            f"{n_samples} samples needs {per_genre} themes/genre but only "
            f"{len(config.THEMES)} themes exist; add themes or lower samples")

    schedule = []
    for genre in config.GENRES:
        themes = rng.sample(config.THEMES, per_genre)
        phrase = genre if "story" in genre else f"{genre} short story"
        for theme in themes:
            schedule.append({
                "genre": genre,
                "theme": theme,
                "prompt": template.format(
                    genre_phrase=phrase, theme_clause=f" involving {theme}"),
            })
    rng.shuffle(schedule)
    return schedule[:n_samples]


def samples_dir(variant: str) -> str:
    if variant == "default":
        return config.SAMPLES_DIR
    return os.path.join(config.OUTPUT_DIR, f"samples_{variant}")


def jsonl_path(model: str, variant: str = "default") -> str:
    safe = model.replace("/", "_")
    return os.path.join(samples_dir(variant), f"{safe}.jsonl")


def count_done(model: str, variant: str = "default") -> int:
    path = jsonl_path(model, variant)
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def run(models: list[str], n_samples: int, dry_run: bool = False,
        assume_yes: bool = False, variant: str = "default") -> None:
    if variant not in config.PROMPT_VARIANTS:
        raise SystemExit(f"unknown variant '{variant}'; choose from "
                         f"{list(config.PROMPT_VARIANTS)}")
    schedule = build_schedule(n_samples, config.RANDOM_SEED,
                              config.PROMPT_VARIANTS[variant])
    if variant != "default":
        print(f"[variant: {variant}] -> {samples_dir(variant)}")

    done = {m: (0 if dry_run else count_done(m, variant)) for m in models}
    remaining = sum(max(0, n_samples - done[m]) for m in models)
    print(f"Models: {len(models)}, samples/model: {n_samples}, "
          f"already done: {sum(done.values())}, calls to make: {remaining}, "
          f"max_tokens: {config.MAX_TOKENS}")

    if remaining > config.MAX_TOTAL_CALLS:
        print(f"ABORT: {remaining} calls exceeds MAX_TOTAL_CALLS="
              f"{config.MAX_TOTAL_CALLS}.")
        if not assume_yes:
            reply = input("Type 'yes' to proceed anyway: ").strip().lower()
            if reply != "yes":
                sys.exit(1)

    if dry_run:
        for i, item in enumerate(schedule):
            print(f"[{i+1:3d}] ({item['genre']}) {item['prompt']}")
        print(f"\n(dry run: {len(schedule)} prompts/model x {len(models)} "
              f"models = {len(schedule) * len(models)} calls, no API calls made)")
        return

    os.makedirs(samples_dir(variant), exist_ok=True)
    falclient.get_fal_key()  # fail fast if the key is missing

    for model in models:
        start = done[model]
        if start >= n_samples:
            print(f"{model}: {start} samples already present, skipping")
            continue
        print(f"\n=== {model} ({start}/{n_samples} done, resuming) ===")
        path = jsonl_path(model, variant)
        failures = 0
        with open(path, "a", encoding="utf-8") as f:
            for i in range(start, n_samples):
                item = schedule[i]
                try:
                    result = falclient.complete(
                        model, item["prompt"],
                        temperature=config.TEMPERATURE,
                        max_tokens=config.MAX_TOKENS)
                except falclient.FalError as e:
                    failures += 1
                    print(f"  [{i+1}] FAILED: {e}")
                    if failures >= 5:
                        print(f"  {model}: 5 failures, moving to next model "
                              f"(rerun to resume)")
                        break
                    continue
                record = {
                    "model": model,
                    "genre": item["genre"],
                    "theme": item["theme"],
                    "prompt": item["prompt"],
                    "completion": result.get("output", ""),
                    "timestamp": datetime.datetime.now(
                        datetime.timezone.utc).isoformat(),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                if (i + 1) % 20 == 0 or i + 1 == n_samples:
                    print(f"  {i+1}/{n_samples}")
        print(f"{model}: {count_done(model, variant)} samples on disk")
