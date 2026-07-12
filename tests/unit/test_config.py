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
        """OPENAI_MODEL should be a non-empty string."""
        from backend.core.config import OPENAI_MODEL
        assert isinstance(OPENAI_MODEL, str)
        assert len(OPENAI_MODEL) > 0

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

    @pytest.mark.parametrize("config_attr,expected", [
        ("SONIOX_API_KEY", "test-soniox-key"),
        ("OPENAI_API_KEY", "test-openai-key"),
        ("OPENAI_MODEL", "test-openai-model"),
    ])
    def test_config_attr_writable(self, config_attr, expected):
        """Config attributes should be assignable (e.g. for tests)."""
        import backend.core.config as cfg
        original = getattr(cfg, config_attr)
        try:
            setattr(cfg, config_attr, expected)
            assert getattr(cfg, config_attr) == expected
        finally:
            setattr(cfg, config_attr, original)

    def test_config_accepts_empty_key(self):
        """Config attributes can be set to empty string."""
        import backend.core.config as cfg
        # Verify we can clear and restore a key
        original = cfg.OPENAI_API_KEY
        try:
            cfg.OPENAI_API_KEY = ""
            assert cfg.OPENAI_API_KEY == ""
        finally:
            cfg.OPENAI_API_KEY = original
