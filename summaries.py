"""
Summary and translation utilities for article processing.

Provides functions for generating and caching Danish summaries.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, Tuple

from logger import get_logger

logger = get_logger(__name__)

_openai_client = None
_openai_lock = threading.Lock()


def _get_openai_client():
    """Lazily initialize the OpenAI client when an API key is available."""
    global _openai_client

    with _openai_lock:
        if _openai_client is not None:
            return _openai_client

        try:
            import openai  # type: ignore
        except ImportError:
            logger.debug("OpenAI library not available; Danish summaries will use English text")
            _openai_client = None
            return None

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            logger.debug("OPENAI_API_KEY not configured; skipping Danish summary generation")
            _openai_client = None
            return None

        try:
            _openai_client = openai.OpenAI(api_key=api_key)
            logger.debug("OpenAI client initialised for Danish summaries")
        except Exception as exc:
            logger.warning(f"Failed to initialise OpenAI client for summaries: {exc}")
            _openai_client = None

        return _openai_client


def load_danish_summary_cache(cache_path: Path) -> Dict[str, str]:
    """Load cached Danish summaries from disk."""
    if not cache_path.exists():
        return {}

    try:
        with cache_path.open("r", encoding="utf-8") as handle:
            cache: Dict[str, str] = json.load(handle)
            return cache
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning(f"Failed to load Danish summary cache {cache_path}: {exc}")
        return {}


def save_danish_summary_cache(cache_path: Path, cache: Dict[str, str]) -> None:
    """Persist Danish summary cache to disk."""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as handle:
            json.dump(cache, handle, ensure_ascii=False, indent=2)
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning(f"Failed to save Danish summary cache {cache_path}: {exc}")


def translate_summary_to_danish(
    english_summary: str,
    url: str,
    cache: Dict[str, str],
    *,
    force: bool = False,
) -> Tuple[str, bool]:
    """
    Translate an English summary to Danish, using cache where possible.

    Args:
        english_summary: Summary text in English.
        url: Article URL used as cache key.
        cache: Shared dictionary of cached translations.
        force: When True, bypass cache and refresh translation.

    Returns:
        Tuple[str, bool]: (Danish summary text, cache_updated_flag)
    """
    if not english_summary:
        return "", False

    cache_key = url or english_summary

    if not force and cache_key in cache:
        return cache[cache_key], False

    client = _get_openai_client()
    if client is None:
        cache[cache_key] = english_summary
        return english_summary, True

    prompt = (
        "Translate the following English article summary to Danish. "
        "Maintain the original meaning, tone, and nuances.\n\n"
        f"English summary:\n{english_summary}\n\nDanish translation:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional English-to-Danish translator. "
                        "Translate the provided summary accurately."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )

        danish_summary = response.choices[0].message.content.strip()

        if not danish_summary:
            danish_summary = english_summary

        cache[cache_key] = danish_summary

        time.sleep(0.1)

        return danish_summary, True

    except Exception as exc:
        logger.warning(f"Failed to translate summary for {url[:80]}: {exc}")
        cache[cache_key] = english_summary
        return english_summary, True


