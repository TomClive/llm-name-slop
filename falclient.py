"""Minimal HTTP client for fal-ai/any-llm with retry and backoff."""

import os
import random
import time

import requests

import config


class FalError(Exception):
    pass


def get_fal_key() -> str:
    key = os.environ.get("FAL_KEY")
    if key:
        return key
    # The key is set at Windows user scope; child shells started earlier
    # don't inherit it, so fall back to reading HKCU\Environment directly.
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                key, _ = winreg.QueryValueEx(k, "FAL_KEY")
                if key:
                    return key
        except OSError:
            pass
    raise FalError("FAL_KEY not found in environment or HKCU\\Environment")


_session = requests.Session()


def complete(model: str, prompt: str, *, temperature: float | None,
             max_tokens: int, retries: int = 5) -> dict:
    """One completion. Returns the response dict (keys: output, error, ...).

    Retries on 429/5xx/network errors with exponential backoff. If the
    provider rejects the temperature parameter, retries once without it
    (provider default is documented to be >= 0.8 territory for chat models).
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "priority": "throughput",
    }
    if temperature is not None:
        payload["temperature"] = temperature

    headers = {
        "Authorization": f"Key {get_fal_key()}",
        "Content-Type": "application/json",
    }

    last_err = None
    for attempt in range(retries):
        try:
            resp = _session.post(config.FAL_ENDPOINT, json=payload,
                                 headers=headers, timeout=120)
        except requests.RequestException as e:
            last_err = f"network error: {e}"
        else:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("error"):
                    last_err = f"model error: {data['error']}"
                else:
                    return data
            elif resp.status_code == 400 and "temperature" in resp.text.lower() \
                    and "temperature" in payload:
                del payload["temperature"]
                continue  # immediate retry without temperature, no backoff
            elif resp.status_code in (401, 403):
                raise FalError(f"auth failed ({resp.status_code}): {resp.text[:300]}")
            elif resp.status_code == 422:
                raise FalError(f"bad request (422): {resp.text[:300]}")
            else:
                last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"

        sleep = min(60.0, (2 ** attempt) + random.uniform(0, 1))
        time.sleep(sleep)

    raise FalError(f"giving up on {model} after {retries} attempts: {last_err}")
