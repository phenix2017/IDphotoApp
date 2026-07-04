"""Background-removal backend selection.

The processing code still uses environment flags internally, but this module
keeps that policy out of UI code and gives callers a single explicit option.
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Iterator


BACKGROUND_ENGINES = (
    "Best quality (slower)",
    "Fast (recommended)",
    "Basic (no AI model)",
)

# Streamlit runs each session in its own thread within one process, so the
# env-var toggling below is process-wide shared state. Without this lock, two
# concurrent requests picking different engines can interleave: one thread's
# flags get overwritten mid-inference by another, silently swapping which
# model actually runs — and since callers cache results by engine name
# (st.cache_data), the wrong output can get stored under the wrong key.
_engine_lock = threading.Lock()


@contextmanager
def selected_background_engine(engine: str) -> Iterator[None]:
    _engine_lock.acquire()
    old_disable_birefnet = os.environ.get("IDPHOTO_DISABLE_BIREFNET")
    old_disable_rembg = os.environ.get("IDPHOTO_DISABLE_REMBG")
    try:
        if engine == "Best quality (slower)":
            os.environ.pop("IDPHOTO_DISABLE_BIREFNET", None)
            os.environ.pop("IDPHOTO_DISABLE_REMBG", None)
        elif engine == "Fast (recommended)":
            os.environ["IDPHOTO_DISABLE_BIREFNET"] = "1"
            os.environ.pop("IDPHOTO_DISABLE_REMBG", None)
        else:
            os.environ["IDPHOTO_DISABLE_BIREFNET"] = "1"
            os.environ["IDPHOTO_DISABLE_REMBG"] = "1"
        yield
    finally:
        if old_disable_birefnet is None:
            os.environ.pop("IDPHOTO_DISABLE_BIREFNET", None)
        else:
            os.environ["IDPHOTO_DISABLE_BIREFNET"] = old_disable_birefnet
        if old_disable_rembg is None:
            os.environ.pop("IDPHOTO_DISABLE_REMBG", None)
        else:
            os.environ["IDPHOTO_DISABLE_REMBG"] = old_disable_rembg
        _engine_lock.release()
