"""
glas_mcp/skills/base.py

Dynamic skill loader. Scans skills/ for subdirectories containing
skill.yaml + skill.md and exposes them as SkillDef objects.

Usage:
    from glas_mcp.skills.base import SkillsLoader
    loader = SkillsLoader()
    all_skills = loader.load_all()          # dict[name, SkillDef]
    prompt_hint = loader.agent_hint()       # one-line summary for agent system prompt
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml


@dataclass
class SkillDef:
    name: str
    tool: str
    description: str
    version: str
    tags: List[str]
    content_md: str          # full skill.md text
    skill_dir: str


class SkillsLoader:
    """
    Auto-discovers every *_skill/ subdirectory under the skills/ root.
    A valid skill directory must contain both skill.yaml and skill.md.
    """

    def __init__(self, skills_root: Optional[str] = None):
        if skills_root is None:
            skills_root = os.path.join(os.path.dirname(__file__))
        self.skills_root = skills_root
        self._skills: Dict[str, SkillDef] = {}

    def load_all(self) -> Dict[str, SkillDef]:
        self._skills = {}
        for entry in os.scandir(self.skills_root):
            if not entry.is_dir() or entry.name.startswith("__"):
                continue
            yaml_path = os.path.join(entry.path, "skill.yaml")
            md_path   = os.path.join(entry.path, "skill.md")
            if not os.path.exists(yaml_path) or not os.path.exists(md_path):
                continue
            try:
                with open(yaml_path) as f:
                    cfg = yaml.safe_load(f) or {}
                with open(md_path, encoding="utf-8") as f:
                    content = f.read()
                skill = SkillDef(
                    name        = cfg.get("name", entry.name),
                    tool        = cfg.get("tool", ""),
                    description = cfg.get("description", ""),
                    version     = str(cfg.get("version", "1.0.0")),
                    tags        = list(cfg.get("tags", [])),
                    content_md  = content,
                    skill_dir   = entry.path,
                )
                self._skills[skill.name] = skill
            except Exception:
                continue
        return self._skills

    def get(self, name: str) -> Optional[SkillDef]:
        return self._skills.get(name)

    def list_names(self) -> List[str]:
        return sorted(self._skills.keys())

    def agent_hint(self) -> str:
        """One-line summary injected into the agent system prompt."""
        if not self._skills:
            return "No skills loaded."
        parts = [f"{s.name} ({s.description})" for s in self._skills.values()]
        return (
            "Available Glas MCP skills: "
            + "; ".join(parts)
            + ". Use these skills to guide your tool usage for quality output."
        )

    def to_api_list(self) -> List[Dict]:
        return [
            {
                "name":        s.name,
                "tool":        s.tool,
                "description": s.description,
                "version":     s.version,
                "tags":        s.tags,
            }
            for s in self._skills.values()
        ]
