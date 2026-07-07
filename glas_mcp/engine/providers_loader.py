"""
glas_mcp/engine/providers_loader.py

Auto-discovers AI provider configurations from
  glas_mcp/providers/<Name>/provider.yaml

Each provider.yaml declares:
  - name, display_name, logo, color
  - api_base_url, auth_type, auth_header/auth_param
  - extra_headers, supports_tool_use
  - request_format, response_format
  - models list with id, label, context_window, default

Usage:
    loader = ProvidersLoader(PROVIDERS_ROOT)
    providers = loader.load_all()   # dict[name, dict]
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import yaml


class ProvidersLoader:
    """
    Scans the providers root directory and loads all provider.yaml files.

    Directory layout expected:
        providers/
          Anthropic/
            provider.yaml
          Google/
            provider.yaml
          Groq/
            provider.yaml
          OpenRouter/
            provider.yaml
    """

    def __init__(self, providers_root: str):
        self.providers_root = providers_root
        self._providers: Dict[str, dict] = {}

    # ── Public API ───────────────────────────────────────────────────────────

    def load_all(self) -> Dict[str, dict]:
        """
        Scan providers_root for subdirectories containing provider.yaml.
        Returns dict keyed by provider name (from YAML, not folder name).
        """
        self._providers.clear()

        if not os.path.isdir(self.providers_root):
            return {}

        for entry in sorted(os.scandir(self.providers_root), key=lambda e: e.name):
            if not entry.is_dir() or entry.name.startswith("_"):
                continue

            yaml_path = os.path.join(entry.path, "provider.yaml")
            if not os.path.exists(yaml_path):
                continue

            try:
                provider = self._load_yaml(yaml_path, folder=entry.name)
                name = provider["name"]
                self._providers[name] = provider
                print(f"[Glas MCP] Provider loaded: {provider['display_name']} ({len(provider.get('models', []))} models)")
            except Exception as exc:
                print(f"[Glas MCP] Warning: could not load provider from {yaml_path}: {exc}")

        return self._providers

    def get(self, name: str) -> Optional[dict]:
        return self._providers.get(name)

    def list_all(self) -> List[dict]:
        """Return providers as list, safe to serialise (no internal keys)."""
        return [self._public(p) for p in self._providers.values()]

    def names(self) -> List[str]:
        return list(self._providers.keys())

    # ── Private helpers ──────────────────────────────────────────────────────

    def _load_yaml(self, path: str, folder: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("provider.yaml must be a YAML mapping")

        required = ("name", "display_name", "api_base_url", "models")
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing required keys: {missing}")

        # Normalise models: ensure default_model is set
        models: list = data.get("models", [])
        default_model = data.get("default_model")
        if not default_model:
            for m in models:
                if m.get("default"):
                    default_model = m["id"]
                    break
            if not default_model and models:
                default_model = models[0]["id"]
            data["default_model"] = default_model

        # Attach folder name for reference
        data["_folder"] = folder

        return data

    def _public(self, provider: dict) -> dict:
        """Strip internal keys before sending to client."""
        return {k: v for k, v in provider.items() if not k.startswith("_")}
