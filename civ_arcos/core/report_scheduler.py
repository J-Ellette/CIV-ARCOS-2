"""Scheduled report metadata store with lightweight persistence."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast


@dataclass
class ReportJob:
    """Metadata for a scheduled report job."""

    job_id: str
    report_type: str
    frequency: str
    target: str
    created_at: str
    next_run_at: str
    status: str = "scheduled"


class ReportScheduler:
    """Manage scheduled report metadata with file-backed persistence."""

    _SUPPORTED_FREQUENCIES = {
        "hourly": timedelta(hours=1),
        "daily": timedelta(days=1),
        "weekly": timedelta(days=7),
        "monthly": timedelta(days=30),
    }

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._lock = threading.RLock()
        self._storage_path = storage_path or Path(".civ_arcos") / "report_jobs.json"
        self._jobs: Dict[str, ReportJob] = {}
        self._load()

    def schedule_report(
        self,
        report_type: str,
        frequency: str,
        target: str,
    ) -> ReportJob:
        """Create and persist a scheduled report job metadata record."""
        normalized_frequency = frequency.lower()
        if normalized_frequency not in self._SUPPORTED_FREQUENCIES:
            raise ValueError(
                "Unsupported frequency. Use one of: "
                f"{', '.join(self._SUPPORTED_FREQUENCIES.keys())}"
            )

        now = datetime.now(timezone.utc)
        next_run = now + self._SUPPORTED_FREQUENCIES[normalized_frequency]

        job = ReportJob(
            job_id=f"rpt_{uuid.uuid4().hex[:12]}",
            report_type=report_type,
            frequency=normalized_frequency,
            target=target,
            created_at=now.isoformat(),
            next_run_at=next_run.isoformat(),
            status="scheduled",
        )

        with self._lock:
            self._jobs[job.job_id] = job
            self._save()

        return job

    def list_jobs(self) -> List[Dict[str, str]]:
        """Return scheduled report job metadata sorted by creation timestamp."""
        with self._lock:
            jobs = [asdict(job) for job in self._jobs.values()]
        jobs.sort(key=lambda item: item["created_at"], reverse=True)
        return jobs

    def get_job(self, job_id: str) -> Optional[Dict[str, str]]:
        """Return a single scheduled report job metadata record by ID."""
        with self._lock:
            job = self._jobs.get(job_id)
            return asdict(job) if job else None

    def _load(self) -> None:
        """Load persisted report metadata from disk when present."""
        if not self._storage_path.exists():
            return

        raw = self._storage_path.read_text(encoding="utf-8")
        data_obj: Any = json.loads(raw)
        if not isinstance(data_obj, list):
            return
        data_list = cast(List[object], data_obj)

        for item_obj in data_list:
            if not isinstance(item_obj, dict):
                continue
            item = cast(Dict[str, object], item_obj)
            required = {
                "job_id",
                "report_type",
                "frequency",
                "target",
                "created_at",
                "next_run_at",
                "status",
            }
            if not required.issubset(set(item.keys())):
                continue
            if not all(isinstance(item[key], str) for key in required):
                continue

            job_id = cast(str, item["job_id"])
            report_type = cast(str, item["report_type"])
            frequency = cast(str, item["frequency"])
            target = cast(str, item["target"])
            created_at = cast(str, item["created_at"])
            next_run_at = cast(str, item["next_run_at"])
            status = cast(str, item["status"])

            job = ReportJob(
                job_id=job_id,
                report_type=report_type,
                frequency=frequency,
                target=target,
                created_at=created_at,
                next_run_at=next_run_at,
                status=status,
            )
            self._jobs[job.job_id] = job

    def _save(self) -> None:
        """Persist report job metadata atomically."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(job) for job in self._jobs.values()]
        temp_path = self._storage_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp_path.replace(self._storage_path)
