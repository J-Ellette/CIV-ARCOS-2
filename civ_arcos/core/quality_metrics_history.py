"""Quality metrics history persistence and trend calculations."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast


@dataclass
class QualityMetricSnapshot:
    """A single persisted quality metric point-in-time snapshot."""

    snapshot_id: str
    timestamp: str
    score: float
    evidence_total: int
    risk_components: int
    source: str


class QualityMetricsHistory:
    """Manage quality metrics snapshots with simple file-backed persistence."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._lock = threading.RLock()
        self._storage_path = (
            storage_path or Path(".civ_arcos") / "quality_metrics_history.json"
        )
        self._snapshots: List[QualityMetricSnapshot] = []
        self._load()

    def record_snapshot(
        self,
        score: float,
        evidence_total: int,
        risk_components: int,
        source: str,
    ) -> Dict[str, Any]:
        """Persist a quality metrics snapshot and return serialized metadata."""
        snapshot = QualityMetricSnapshot(
            snapshot_id=f"qms_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            score=float(score),
            evidence_total=int(evidence_total),
            risk_components=int(risk_components),
            source=source,
        )
        with self._lock:
            self._snapshots.append(snapshot)
            self._save()
        return asdict(snapshot)

    def list_snapshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return latest persisted snapshots ordered by timestamp descending."""
        safe_limit = max(1, limit)
        with self._lock:
            ordered = sorted(self._snapshots, key=lambda s: s.timestamp, reverse=True)
            return [asdict(s) for s in ordered[:safe_limit]]

    def trend_summary(self, window: int = 10) -> Dict[str, Any]:
        """Return deterministic trend summary over the latest window of snapshots."""
        points = self.list_snapshots(limit=max(2, window))
        if not points:
            return {
                "count": 0,
                "current_score": None,
                "previous_score": None,
                "delta_score": None,
                "average_score": None,
                "points": [],
            }

        current_score = points[0]["score"]
        previous_score = points[1]["score"] if len(points) > 1 else None
        delta_score = (
            round(current_score - previous_score, 2)
            if previous_score is not None
            else None
        )
        average_score = round(
            sum(cast(float, p["score"]) for p in points) / len(points),
            2,
        )

        return {
            "count": len(points),
            "current_score": current_score,
            "previous_score": previous_score,
            "delta_score": delta_score,
            "average_score": average_score,
            "points": points,
        }

    def forecast_summary(self, window: int = 10, horizon: int = 3) -> Dict[str, Any]:
        """Return a deterministic linear quality forecast from recent snapshots."""
        safe_window = max(2, int(window))
        safe_horizon = max(1, min(int(horizon), 12))
        points = self.list_snapshots(limit=safe_window)

        if not points:
            return {
                "count": 0,
                "window": safe_window,
                "horizon": safe_horizon,
                "current_score": None,
                "trend_slope": 0.0,
                "average_score": None,
                "forecast": [],
                "points": [],
            }

        ordered = list(reversed(points))
        scores = [float(point["score"]) for point in ordered]
        current_score = float(points[0]["score"])

        slope = 0.0
        if len(scores) > 1:
            deltas = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
            slope = sum(deltas) / len(deltas)

        average_score = round(sum(scores) / len(scores), 2)
        forecast = []
        for step in range(1, safe_horizon + 1):
            projected = max(0.0, min(100.0, current_score + slope * step))
            forecast.append(
                {
                    "step": step,
                    "projected_score": round(projected, 2),
                }
            )

        return {
            "count": len(points),
            "window": safe_window,
            "horizon": safe_horizon,
            "current_score": current_score,
            "trend_slope": round(slope, 4),
            "average_score": average_score,
            "forecast": forecast,
            "points": points,
        }

    def _load(self) -> None:
        """Load persisted snapshots when available."""
        if not self._storage_path.exists():
            return

        raw = self._storage_path.read_text(encoding="utf-8")
        data_obj: Any = json.loads(raw)
        if not isinstance(data_obj, list):
            return

        data_list = cast(List[object], data_obj)
        required = {
            "snapshot_id",
            "timestamp",
            "score",
            "evidence_total",
            "risk_components",
            "source",
        }
        for item_obj in data_list:
            if not isinstance(item_obj, dict):
                continue
            item = cast(Dict[str, object], item_obj)
            if not required.issubset(set(item.keys())):
                continue
            if not isinstance(item["snapshot_id"], str):
                continue
            if not isinstance(item["timestamp"], str):
                continue
            if not isinstance(item["score"], (int, float)):
                continue
            if not isinstance(item["evidence_total"], int):
                continue
            if not isinstance(item["risk_components"], int):
                continue
            if not isinstance(item["source"], str):
                continue

            self._snapshots.append(
                QualityMetricSnapshot(
                    snapshot_id=cast(str, item["snapshot_id"]),
                    timestamp=cast(str, item["timestamp"]),
                    score=float(item["score"]),
                    evidence_total=cast(int, item["evidence_total"]),
                    risk_components=cast(int, item["risk_components"]),
                    source=cast(str, item["source"]),
                )
            )

    def _save(self) -> None:
        """Persist snapshots atomically."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(snapshot) for snapshot in self._snapshots]
        tmp_path = self._storage_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self._storage_path)
