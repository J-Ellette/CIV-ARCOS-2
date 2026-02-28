"""GSN visualizer — produces SVG, DOT, and summary output."""

from typing import Any, Dict

from civ_arcos.assurance.case import AssuranceCase
from civ_arcos.assurance.gsn import GSNNodeType

# Color / shape mapping per node type
_STYLE: Dict[GSNNodeType, Dict[str, str]] = {
    GSNNodeType.GOAL: {"fill": "#4caf50", "shape": "rect", "label": "G"},
    GSNNodeType.STRATEGY: {"fill": "#2196f3", "shape": "parallelogram", "label": "S"},
    GSNNodeType.SOLUTION: {"fill": "#ffc107", "shape": "circle", "label": "Sn"},
    GSNNodeType.CONTEXT: {"fill": "#9e9e9e", "shape": "rounded_rect", "label": "C"},
    GSNNodeType.ASSUMPTION: {"fill": "#e91e63", "shape": "rounded_rect", "label": "A"},
    GSNNodeType.JUSTIFICATION: {
        "fill": "#9c27b0",
        "shape": "rounded_rect",
        "label": "J",
    },
}

_DOT_SHAPE: Dict[GSNNodeType, str] = {
    GSNNodeType.GOAL: "box",
    GSNNodeType.STRATEGY: "parallelogram",
    GSNNodeType.SOLUTION: "ellipse",
    GSNNodeType.CONTEXT: "box",
    GSNNodeType.ASSUMPTION: "box",
    GSNNodeType.JUSTIFICATION: "box",
}


class GSNVisualizer:
    """Render an AssuranceCase as SVG, DOT, or summary."""

    # ------------------------------------------------------------------
    # SVG
    # ------------------------------------------------------------------
    def to_svg(self, case: AssuranceCase) -> str:
        nodes = case.traverse()
        if not nodes:
            return (
                "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='60'>"
                "<text x='10' y='30'>Empty case</text></svg>"
            )

        # Simple vertical tree layout
        x_spacing = 220
        y_spacing = 100
        node_w = 180
        node_h = 60

        # Assign positions via BFS level order
        positions: Dict[str, tuple] = {}
        levels: Dict[str, int] = {}
        root_id = case.root_goal_id or nodes[0].id

        def _assign(nid: str, level: int, order: int) -> None:
            if nid in positions:
                return
            levels[nid] = level
            positions[nid] = (order * x_spacing + 30, level * y_spacing + 30)
            node = case.nodes.get(nid)
            if node:
                for i, child_id in enumerate(node.children):
                    _assign(child_id, level + 1, order * max(1, len(node.children)) + i)

        _assign(root_id, 0, 0)
        # Any unreached nodes
        for node in nodes:
            if node.id not in positions:
                positions[node.id] = (
                    30,
                    (
                        (max(v[1] for v in positions.values()) + y_spacing)
                        if positions
                        else 30
                    ),
                )

        max_x = max(p[0] for p in positions.values()) + node_w + 30
        max_y = max(p[1] for p in positions.values()) + node_h + 30

        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_x}" height="{max_y}">',
            '<defs><marker id="arrow" markerWidth="8" markerHeight="8" '
            'refX="6" refY="3" orient="auto">'
            '<path d="M0,0 L0,6 L6,3 z" fill="#555"/></marker></defs>',
        ]

        # Edges
        for node in nodes:
            if node.id not in positions:
                continue
            px, py = positions[node.id]
            for child_id in node.children:
                if child_id in positions:
                    cx, cy = positions[child_id]
                    lines.append(
                        f'<line x1="{px + node_w // 2}" y1="{py + node_h}" '
                        f'x2="{cx + node_w // 2}" y2="{cy}" '
                        f'stroke="#555" stroke-width="1.5" '
                        f'marker-end="url(#arrow)"/>'
                    )

        # Nodes
        for node in nodes:
            if node.id not in positions:
                continue
            x, y = positions[node.id]
            style = _STYLE.get(node.node_type, _STYLE[GSNNodeType.GOAL])
            fill = style["fill"]
            label = style["label"]
            text = (
                (node.statement[:28] + "…")
                if len(node.statement) > 30
                else node.statement
            )
            escaped = (
                text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            lines.append(
                f'<rect x="{x}" y="{y}" width="{node_w}" height="{node_h}" '
                f'rx="6" fill="{fill}" stroke="#333" stroke-width="1"/>'
            )
            lines.append(
                f'<text x="{x + 6}" y="{y + 20}" font-size="10" fill="white" font-weight="bold">'
                f"[{label}]</text>"
            )
            lines.append(
                f'<text x="{x + 6}" y="{y + 38}" font-size="9" fill="white">{escaped}</text>'
            )

        lines.append("</svg>")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # DOT
    # ------------------------------------------------------------------
    def to_dot(self, case: AssuranceCase) -> str:
        lines = [
            f'digraph "{case.title or case.case_id}" {{',
            "  rankdir=TB;",
            "  node [fontsize=10];",
        ]
        for node in case.nodes.values():
            shape = _DOT_SHAPE.get(node.node_type, "box")
            label = node.statement.replace('"', '\\"')[:50]
            lines.append(f'  "{node.id}" [label="{label}" shape={shape}];')
        for node in case.nodes.values():
            for child_id in node.children:
                lines.append(f'  "{node.id}" -> "{child_id}";')
        lines.append("}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def generate_summary(self, case: AssuranceCase) -> Dict[str, Any]:
        node_types: Dict[str, int] = {}
        evidence_count = 0
        for node in case.nodes.values():
            key = node.node_type.value
            node_types[key] = node_types.get(key, 0) + 1
            evidence_count += len(node.evidence_ids)

        # Max depth via BFS
        def _depth(nid: str, visited: set) -> int:
            if nid not in case.nodes or nid in visited:
                return 0
            visited.add(nid)
            node = case.nodes[nid]
            if not node.children:
                return 1
            return 1 + max((_depth(c, visited) for c in node.children), default=0)

        root_id = case.root_goal_id
        max_depth = _depth(root_id, set()) if root_id else 0

        return {
            "case_id": case.case_id,
            "title": case.title,
            "node_count": len(case.nodes),
            "node_types": node_types,
            "evidence_count": evidence_count,
            "max_depth": max_depth,
            "has_root": root_id is not None,
        }
