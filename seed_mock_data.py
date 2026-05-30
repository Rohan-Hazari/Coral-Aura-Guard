"""
seed_mock_data.py — Mock Data Seeder for Aura Guard

Generates local JSON fixture files that mimic OSV and GitHub API responses
for offline development and testing. Makes NO HTTP requests to any external
endpoint.

Usage:
    python seed_mock_data.py
"""

from __future__ import annotations

import json
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def seed_osv_mock() -> None:
    """Write a mock OSV vulnerability record for lodash@4.17.15 to fixtures/osv.json."""
    data = [
        {
            "cve_id": "CVE-2021-23337",
            "vulnerability_details": (
                "Prototype pollution in lodash 4.17.15 and earlier via the "
                "zipObjectDeep function. An attacker can supply a specially "
                "crafted object to pollute the prototype of Object."
            ),
            "risk_level": "CRITICAL",
            "package_name": "lodash",
            "version": "4.17.15",
            "ecosystem": "npm",
            "summary": "Prototype pollution in lodash via zipObjectDeep",
            "severity": "CRITICAL",
            "filename": "package.json",
        }
    ]
    _write_fixture("osv.json", data)
    print("Seeded fixtures/osv.json")


def seed_github_pr_mock() -> None:
    """Write a mock GitHub PR file record to fixtures/github_files.json."""
    data = [
        {
            "filename": "package.json",
            "status": "modified",
            "patch": (
                '@@ -10,7 +10,7 @@ "dependencies": {\n'
                '-    "lodash": "^4.17.14",\n'
                '+    "lodash": "^4.17.15",\n'
                '     "express": "^4.18.2"\n'
                "   }"
            ),
            "pull_number": 1042,
            "owner": "acme",
            "repo": "payment-gateway-service",
            "content": json.dumps(
                {
                    "name": "payment-gateway-service",
                    "version": "1.0.0",
                    "dependencies": {
                        "lodash": "^4.17.15",
                        "express": "^4.18.2",
                    },
                    "devDependencies": {
                        "jest": "^29.0.0",
                    },
                },
                indent=2,
            ),
        }
    ]
    _write_fixture("github_files.json", data)
    print("Seeded fixtures/github_files.json")


def seed_downstream_mock() -> None:
    """Write mock downstream repo records to fixtures/github_contents.json."""
    data = [
        {
            "downstream_repo": "acme/billing-service",
            "active_pr": 88,
            "developer": "alice",
            "manifest_data": '{"dependencies": {"core-billing-utils": "^2.1.0"}}',
            "import_reference": "core-billing-utils",
            "owner": "acme",
        },
        {
            "downstream_repo": "acme/invoice-processor",
            "active_pr": 102,
            "developer": "bob",
            "manifest_data": '{"dependencies": {"core-billing-utils": "^2.0.5"}}',
            "import_reference": "core-billing-utils",
            "owner": "acme",
        },
        {
            "downstream_repo": "acme/payment-reconciler",
            "active_pr": 57,
            "developer": "carol",
            "manifest_data": '{"dependencies": {"core-billing-utils": "^1.9.0"}}',
            "import_reference": "core-billing-utils",
            "owner": "acme",
        },
    ]
    _write_fixture("github_contents.json", data)
    print("Seeded fixtures/github_contents.json")


def _write_fixture(filename: str, data: object) -> None:
    """Write *data* as JSON to ``fixtures/<filename>``, overwriting if present."""
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


if __name__ == "__main__":
    seed_osv_mock()
    seed_github_pr_mock()
    seed_downstream_mock()
    print("All fixtures seeded successfully.")
