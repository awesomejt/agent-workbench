from __future__ import annotations

import os
import time
import uuid

import pytest
import requests as _requests

BASE_URL = os.environ.get("AWB_API_URL", "http://localhost:8000").rstrip("/")


def _wait_for_api(timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = _requests.get(f"{BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"API at {BASE_URL} did not become healthy within {timeout}s")


@pytest.fixture(scope="session", autouse=True)
def api_ready() -> None:
    _wait_for_api()


@pytest.fixture
def project() -> dict:
    slug = f"itest-{uuid.uuid4().hex[:10]}"
    resp = _requests.post(f"{BASE_URL}/api/projects", json={"name": slug, "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()
