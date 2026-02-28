"""Tests for SVG badge generator."""

import pytest
from civ_arcos.web.badges import BadgeGenerator


def test_coverage_badge_gold():
    gen = BadgeGenerator()
    svg = gen.generate_coverage_badge(97.5)
    assert "#ffd700" in svg
    assert "97.5%" in svg


def test_coverage_badge_silver():
    gen = BadgeGenerator()
    svg = gen.generate_coverage_badge(85.0)
    assert "#c0c0c0" in svg


def test_coverage_badge_bronze():
    gen = BadgeGenerator()
    svg = gen.generate_coverage_badge(70.0)
    assert "#cd7f32" in svg


def test_security_badge_secure():
    gen = BadgeGenerator()
    svg = gen.generate_security_badge(0)
    assert "secure" in svg
    assert "#44cc11" in svg


def test_security_badge_vulnerable():
    gen = BadgeGenerator()
    svg = gen.generate_security_badge(5)
    assert "vulns" in svg
    assert "#e05d44" in svg


def test_custom_badge():
    gen = BadgeGenerator()
    svg = gen.generate_custom_badge("build", "passing", "#44cc11")
    assert "build" in svg
    assert "passing" in svg
    assert "#44cc11" in svg


def test_quality_badge():
    gen = BadgeGenerator()
    svg = gen.generate_quality_badge(95)
    assert "quality" in svg
    assert "95" in svg


def test_svg_is_valid_xml():
    gen = BadgeGenerator()
    svg = gen.generate_coverage_badge(88.0)
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
