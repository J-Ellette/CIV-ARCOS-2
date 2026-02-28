"""Tests for configuration system."""
import os
import pytest
from civ_arcos.core import config as config_module


def test_default_config():
    cfg = config_module.Config()
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 8080
    assert cfg.log_level == "INFO"


def test_get_config_returns_singleton():
    cfg1 = config_module.get_config()
    cfg2 = config_module.get_config()
    assert cfg1 is cfg2


def test_config_from_env(monkeypatch):
    config_module._config = None  # reset singleton
    monkeypatch.setenv("CIV_PORT", "9090")
    monkeypatch.setenv("CIV_LOG_LEVEL", "DEBUG")
    cfg = config_module.get_config()
    assert cfg.port == 9090
    assert cfg.log_level == "DEBUG"
    config_module._config = None  # cleanup


def test_config_db_path_default():
    cfg = config_module.Config()
    assert cfg.db_path == "civ_arcos.json"


def test_config_github_token_default():
    cfg = config_module.Config()
    assert cfg.github_token == ""
