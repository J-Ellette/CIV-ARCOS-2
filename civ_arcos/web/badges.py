"""SVG badge generator for CIV-ARCOS metrics."""


class BadgeGenerator:
    """Generates SVG badges for coverage, quality, and security metrics."""

    def generate_coverage_badge(self, coverage_pct: float) -> str:
        if coverage_pct >= 95:
            color = "#ffd700"  # Gold
        elif coverage_pct >= 80:
            color = "#c0c0c0"  # Silver
        else:
            color = "#cd7f32"  # Bronze
        return self._make_svg("coverage", f"{coverage_pct:.1f}%", color)

    def generate_quality_badge(self, score: float) -> str:
        if score >= 90:
            color = "#44cc11"
        elif score >= 70:
            color = "#dfb317"
        else:
            color = "#e05d44"
        return self._make_svg("quality", f"{score:.0f}/100", color)

    def generate_security_badge(self, vuln_count: int) -> str:
        if vuln_count == 0:
            color = "#44cc11"
            value = "secure"
        elif vuln_count <= 3:
            color = "#dfb317"
            value = f"{vuln_count} vulns"
        else:
            color = "#e05d44"
            value = f"{vuln_count} vulns"
        return self._make_svg("security", value, color)

    def generate_custom_badge(self, label: str, value: str, color: str) -> str:
        return self._make_svg(label, value, color)

    def _make_svg(self, label: str, value: str, color: str) -> str:
        label_width = len(label) * 7 + 10
        value_width = len(value) * 7 + 10
        total_width = label_width + value_width
        label_x = label_width // 2
        value_x = label_width + value_width // 2
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">'
            f'<linearGradient id="s" x2="0" y2="100%">'
            f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
            f'<stop offset="1" stop-opacity=".1"/>'
            f'</linearGradient>'
            f'<rect width="{label_width}" height="20" fill="#555"/>'
            f'<rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>'
            f'<rect width="{total_width}" height="20" fill="url(#s)"/>'
            f'<g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">'
            f'<text x="{label_x}" y="15" fill="#010101" fill-opacity=".3">{label}</text>'
            f'<text x="{label_x}" y="14">{label}</text>'
            f'<text x="{value_x}" y="15" fill="#010101" fill-opacity=".3">{value}</text>'
            f'<text x="{value_x}" y="14">{value}</text>'
            f'</g>'
            f'</svg>'
        )
