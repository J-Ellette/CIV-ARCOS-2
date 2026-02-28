"""GitHub REST API adapter using urllib."""
import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from civ_arcos.evidence.collector import Evidence, EvidenceCollector
from civ_arcos.utils import make_evidence


class GitHubCollector(EvidenceCollector):
    """Collects evidence from GitHub repositories."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None) -> None:
        self._token = token
        self._rate_limit_remaining = 60

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "CIV-ARCOS/0.1.0"}
        if self._token:
            headers["Authorization"] = f"token {self._token}"
        return headers

    def _get(self, url: str) -> Optional[Dict[str, Any]]:
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                remaining = resp.headers.get("X-RateLimit-Remaining", "60")
                self._rate_limit_remaining = int(remaining)
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, Exception):
            return None

    def _parse_repo(self, repo_url: str):
        """Extract owner/repo from URL."""
        parts = repo_url.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        return None, None

    def collect(self, repo_url: str = "", token: Optional[str] = None, **kwargs) -> List[Evidence]:  # type: ignore[override]
        if token:
            self._token = token
        owner, repo = self._parse_repo(repo_url)
        if not owner or not repo:
            return self._mock_evidence(repo_url)

        evidence_list: List[Evidence] = []

        # Repo metadata
        repo_data = self._get(f"{self.BASE_URL}/repos/{owner}/{repo}")
        if repo_data is None:
            return self._mock_evidence(repo_url)

        evidence_list.append(self._make_evidence(
            "repository_metadata", repo_url, repo_data,
            {"collector": "GitHubCollector", "endpoint": f"/repos/{owner}/{repo}"}
        ))

        # Commit history (last 10)
        commits = self._get(f"{self.BASE_URL}/repos/{owner}/{repo}/commits?per_page=10")
        if commits:
            evidence_list.append(self._make_evidence(
                "commit_history", repo_url, {"commits": commits[:10]},
                {"collector": "GitHubCollector", "endpoint": f"/repos/{owner}/{repo}/commits"}
            ))

        return evidence_list

    def collect_from_github(self, repo_url: str, commit_hash: str) -> List[Evidence]:
        owner, repo = self._parse_repo(repo_url)
        if not owner or not repo:
            return []
        data = self._get(f"{self.BASE_URL}/repos/{owner}/{repo}/commits/{commit_hash}") or {}
        return [self._make_evidence("commit_detail", repo_url, data,
                                   {"commit_hash": commit_hash})]

    def collect_from_ci(self, build_id: str) -> List[Evidence]:
        return [self._make_evidence("ci_build", "ci_system",
                                   {"build_id": build_id, "status": "unknown"},
                                   {"collector": "GitHubCollector"})]

    def collect_from_security_tools(self, scan_results: Dict[str, Any]) -> List[Evidence]:
        return [self._make_evidence("security_scan", "security_tools", scan_results,
                                   {"collector": "GitHubCollector"})]

    def _make_evidence(self, etype: str, source: str, data: Dict[str, Any],
                       provenance: Dict[str, Any]) -> Evidence:
        return make_evidence(etype, source, data, provenance)

    def _mock_evidence(self, repo_url: str) -> List[Evidence]:
        return [self._make_evidence(
            "repository_metadata", repo_url,
            {"name": "mock-repo", "stars": 0, "language": "Python", "mock": True},
            {"collector": "GitHubCollector", "note": "mock data - API unavailable"}
        )]
