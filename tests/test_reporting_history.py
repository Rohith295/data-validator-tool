import json

from data_validator.models import TabularData, ValidationReport
from data_validator.reporting.history import ReportHistory


def make_report(file_path: str, timestamp: str) -> ValidationReport:
    return ValidationReport(
        file_path=file_path,
        schema_path="schema.json",
        overall_passed=True,
        results=[],
        timestamp=timestamp,
        data_summary=TabularData(
            headers=["id"],
            file_path=file_path,
            encoding_detected="utf-8",
            row_count=1,
            format="csv",
        ),
        total_elapsed_ms=1.0,
    )


class TestReportHistory:
    def test_load_recent_filters_by_file_path(self, tmp_path):
        history = ReportHistory(history_dir=str(tmp_path))
        history.append(make_report("a.csv", "2026-03-22T10:00:00+00:00"))
        history.append(make_report("b.csv", "2026-03-22T11:00:00+00:00"))
        history.append(make_report("a.csv", "2026-03-22T12:00:00+00:00"))

        recent = history.load_recent(file_path="a.csv")

        assert [entry["file_path"] for entry in recent] == ["a.csv", "a.csv"]
        assert [entry["timestamp"] for entry in recent] == [
            "2026-03-22T10:00:00+00:00",
            "2026-03-22T12:00:00+00:00",
        ]

    def test_load_recent_without_filter_returns_all_files(self, tmp_path):
        history_file = tmp_path / "history.json"
        history_file.write_text(
            json.dumps(
                [
                    {"file_path": "a.csv", "timestamp": "1"},
                    {"file_path": "b.csv", "timestamp": "2"},
                ]
            ),
            encoding="utf-8",
        )

        history = ReportHistory(history_dir=str(tmp_path))
        recent = history.load_recent()

        assert [entry["file_path"] for entry in recent] == ["a.csv", "b.csv"]
