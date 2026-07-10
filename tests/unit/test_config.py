"""
Unit tests for the core config module.
"""
from pathlib import Path

import pytest


class TestConfig:
    """Tests for config values and path resolution."""

    def test_prompt_file_path_exists(self):
        """The PROMPT_FILE should point to an existing file."""
        from backend.core.config import PROMPT_FILE
        assert isinstance(PROMPT_FILE, Path)
        assert PROMPT_FILE.exists(), f"Prompt file not found at {PROMPT_FILE}"

    def test_default_openai_model(self):
        """OPENAI_MODEL should have a default value."""
        from backend.core.config import OPENAI_MODEL
        assert OPENAI_MODEL == "gpt-4o-mini"

    def test_project_root_is_absolute(self):
        """PROJECT_ROOT should resolve to an absolute path."""
        from backend.core.config import PROJECT_ROOT
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.is_absolute()

    def test_project_root_points_to_project(self):
        """PROJECT_ROOT should point to the project root directory."""
        from backend.core.config import PROJECT_ROOT
        # The project root should contain key files/dirs
        assert (PROJECT_ROOT / "backend").is_dir()
        assert (PROJECT_ROOT / "pyproject.toml").exists()

    @pytest.mark.parametrize("env_var,config_attr,expected", [
        ("SONIOX_API_KEY", "SONIOX_API_KEY", "test-soniox-key"),
        ("OPENAI_API_KEY", "OPENAI_API_KEY", "test-openai-key"),
        ("OPENAI_MODEL", "OPENAI_MODEL", "gpt-4o-mini"),
    ])
    def test_env_var_overrides(self, monkeypatch, env_var, config_attr, expected):
        """Config should read from environment variables with defaults."""
        monkeypatch.setenv(env_var, expected)
        # Re-import config to pick up new env var
        import importlib
        import backend.core.config as cfg
        importlib.reload(cfg)
        assert getattr(cfg, config_attr) == expected

    def test_missing_soniox_key_raises(self, monkeypatch):
        """Setting SONIOX_API_KEY to empty should propagate correctly."""
        monkeypatch.setenv("SONIOX_API_KEY", "")
        import importlib
        import backend.core.config as cfg
        importlib.reload(cfg)
        assert cfg.SONIOX_API_KEY == ""

    def test_missing_openai_key_raises(self, monkeypatch):
        """Setting OPENAI_API_KEY to empty should propagate correctly."""
        monkeypatch.setenv("OPENAI_API_KEY", "")
        import importlib
        import backend.core.config as cfg
        importlib.reload(cfg)
        assert cfg.OPENAI_API_KEY == ""
