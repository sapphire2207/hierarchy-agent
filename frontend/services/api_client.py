"""API Client for interacting with the Hierarchy & Buying-Role Agent backend."""

import os
from typing import Any, Dict, List, Optional, Tuple
import requests

DEFAULT_BACKEND_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")


class BackendAPIClient:
    """Client for backend FastAPI endpoints."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or DEFAULT_BACKEND_URL).rstrip("/")

    def check_health(self) -> Tuple[bool, str]:
        """
        Checks backend health status via GET /health.
        Returns (is_healthy, status_message).
        """
        url = f"{self.base_url}/health"
        try:
            resp = requests.get(url, timeout=5.0)
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                return True, "Connected to backend successfully"
            return False, f"Unexpected response (HTTP {resp.status_code})"
        except requests.exceptions.ConnectionError:
            return False, f"Cannot reach backend at {self.base_url}. Ensure the FastAPI server is running."
        except Exception as exc:
            return False, f"Health check failed: {str(exc)}"

    def analyze_hierarchy(
        self,
        company: str,
        employees: List[Dict[str, Any]],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Invokes POST /api/v1/hierarchy/analyze.
        Returns (response_data, error_message).
        """
        url = f"{self.base_url}/api/v1/hierarchy/analyze"
        payload = {
            "company": company or "Unknown Company",
            "employees": employees,
        }

        try:
            resp = requests.post(url, json=payload, timeout=60.0)
            if resp.status_code == 200:
                return resp.json(), None

            # Attempt to parse detailed error message
            try:
                err_data = resp.json()
                detail = err_data.get("detail", str(err_data))
            except Exception:
                detail = resp.text

            return None, f"Backend Error (HTTP {resp.status_code}): {detail}"

        except requests.exceptions.Timeout:
            return None, "Request timed out after 60 seconds."
        except requests.exceptions.ConnectionError:
            return None, f"Could not connect to {url}. Please ensure the backend is running."
        except Exception as exc:
            return None, f"Failed to analyze hierarchy: {str(exc)}"
