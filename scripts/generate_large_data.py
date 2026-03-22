"""Generate large CSV and NDJSON validation datasets with known injected errors."""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TARGET_DIR = Path("sample_data")
DEFAULT_SIZE_GB = 10
DEFAULT_BUFFER_ROWS = 100_000
DEFAULT_ERROR_EVERY = 500_000
SEED = 42

HEADERS = [
    "id",
    "name",
    "email",
    "age",
    "salary",
    "active",
    "created_at",
    "country",
]

EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
DATE_RE = r"^\d{4}-\d{2}-\d{2}$"

FIRST_NAMES = [
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Ethan",
    "Farah",
    "Grace",
    "Hugo",
    "Ivy",
    "Jonah",
]
LAST_NAMES = [
    "Smith",
    "Jones",
    "Brown",
    "Wilson",
    "Taylor",
    "Clark",
    "Hall",
    "Lee",
    "Young",
    "King",
]
COUNTRIES = ["NL", "DE", "FR", "ES", "IT", "UK", "US", "CA", "AU", "SE"]


def build_schema() -> dict[str, Any]:
    return {
        "validations": [
            {"columns_check": {"params": HEADERS}},
            {"non_empty_check": {"params": ["id", "name", "email"]}},
            {"types_check": {"params": {"age": "integer", "salary": "float", "active": "bool"}}},
            {
                "range_check": {
                    "params": {
                        "age": {"min": 18, "max": 90},
                        "salary": {"min": 30_000, "max": 200_000},
                    }
                }
            },
            {"regex_check": {"params": {"email": EMAIL_RE, "created_at": DATE_RE}}},
            {"unique_check": {"params": ["id"]}},
        ]
    }


def make_base_row(index: int, rng: random.Random) -> dict[str, str]:
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    age = rng.randint(22, 68)
    salary = round(rng.uniform(45_000, 165_000), 2)
    active = rng.choice(["true", "false"])
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return {
        "id": f"CUST-{index:09d}",
        "name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}.{index}@example.com",
        "age": str(age),
        "salary": f"{salary:.2f}",
        "active": active,
        "created_at": f"2024-{month:02d}-{day:02d}",
        "country": rng.choice(COUNTRIES),
    }


def apply_error(
    row: dict[str, str],
    row_number: int,
    rng: random.Random,
    duplicate_source_id: str,
) -> tuple[str, str]:
    kind = rng.choice(
        [
            "empty_email",
            "empty_name",
            "bad_email",
            "bad_age_type",
            "age_out_of_range",
            "bad_salary_type",
            "salary_out_of_range",
            "bad_bool",
            "bad_date",
            "duplicate_id",
        ]
    )

    if kind == "empty_email":
        row["email"] = ""
        return kind, "non_empty_check, regex_check"
    if kind == "empty_name":
        row["name"] = ""
        return kind, "non_empty_check"
    if kind == "bad_email":
        row["email"] = f"broken-email-{row_number}"
        return kind, "regex_check"
    if kind == "bad_age_type":
        row["age"] = "unknown"
        return kind, "types_check"
    if kind == "age_out_of_range":
        row["age"] = str(rng.choice([4, 112, 150]))
        return kind, "range_check"
    if kind == "bad_salary_type":
        row["salary"] = "not-a-float"
        return kind, "types_check"
    if kind == "salary_out_of_range":
        row["salary"] = str(rng.choice(["250000.00", "999999.99", "-1.00"]))
        return kind, "range_check"
    if kind == "bad_bool":
        row["active"] = "maybe"
        return kind, "types_check"
    if kind == "bad_date":
        row["created_at"] = "2024/99/99"
        return kind, "regex_check"

    row["id"] = duplicate_source_id
    return kind, "unique_check"


def row_to_csv(row: dict[str, str]) -> str:
    return ",".join(row[h] for h in HEADERS)


def row_to_ndjson(row: dict[str, str]) -> str:
    return json.dumps(row, separators=(",", ":"))


def bytes_to_gb(size: int) -> float:
    return size / (1024**3)


def write_schema_and_manifest(
    schema_path: Path,
    manifest_path: Path,
    schema: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def generate_dataset(
    output_path: Path,
    schema_path: Path,
    manifest_path: Path,
    *,
    fmt: str,
    target_bytes: int,
    error_every: int,
    buffer_rows: int,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    serializer = row_to_csv if fmt == "csv" else row_to_ndjson
    header_bytes = 0

    if fmt == "csv":
        header = ",".join(HEADERS) + "\n"
        header_bytes = len(header.encode("utf-8"))

    bytes_written = header_bytes
    rows_written = 0
    duplicate_source_id = "CUST-000000001"
    buffer: list[str] = []
    error_counts: Counter[str] = Counter()
    error_rows: dict[str, list[int]] = defaultdict(list)
    error_checks: dict[str, str] = {}
    start = time.time()

    with output_path.open("w", encoding="utf-8", buffering=8 * 1024 * 1024) as f:
        if fmt == "csv":
            f.write(header)

        while bytes_written < target_bytes:
            row_number = rows_written + 1
            row = make_base_row(row_number, rng)

            if row_number > 1 and row_number % error_every == 0:
                error_kind, expected_check = apply_error(row, row_number, rng, duplicate_source_id)
                error_counts[error_kind] += 1
                error_checks[error_kind] = expected_check
                if len(error_rows[error_kind]) < 10:
                    error_rows[error_kind].append(row_number)

            serialized = serializer(row)
            buffer.append(serialized)
            bytes_written += len(serialized.encode("utf-8")) + 1
            rows_written += 1

            if len(buffer) >= buffer_rows:
                f.write("\n".join(buffer))
                f.write("\n")
                buffer.clear()

                if rows_written % (buffer_rows * 10) == 0:
                    elapsed = time.time() - start
                    print(
                        f"{fmt.upper():<6} rows={rows_written:>12,} "
                        f"size={bytes_to_gb(bytes_written):>6.2f} GB "
                        f"errors={sum(error_counts.values()):>5} "
                        f"time={elapsed:>6.0f}s"
                    )

        if buffer:
            f.write("\n".join(buffer))
            f.write("\n")

    elapsed = round(time.time() - start, 2)
    schema = build_schema()
    summary = {
        "format": fmt,
        "seed": seed,
        "target_size_bytes": target_bytes,
        "actual_size_bytes": output_path.stat().st_size,
        "rows_written": rows_written,
        "error_every": error_every,
        "error_counts": dict(error_counts),
        "expected_checks_by_error": error_checks,
        "sample_error_rows": dict(error_rows),
        "schema_path": schema_path.as_posix(),
        "output_path": output_path.as_posix(),
    }
    write_schema_and_manifest(schema_path, manifest_path, schema, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate large CSV and NDJSON files with deterministic validation errors.",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "ndjson", "both"],
        default="both",
        help="Which file format to generate.",
    )
    parser.add_argument(
        "--size-gb",
        type=float,
        default=DEFAULT_SIZE_GB,
        help="Approximate target size per generated file.",
    )
    parser.add_argument(
        "--error-every",
        type=int,
        default=DEFAULT_ERROR_EVERY,
        help="Inject one error every N rows.",
    )
    parser.add_argument(
        "--buffer-rows",
        type=int,
        default=DEFAULT_BUFFER_ROWS,
        help="Rows to buffer in memory before writing.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help="Seed for deterministic data generation.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=TARGET_DIR,
        help="Directory for generated files, schemas, and manifests.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_bytes = int(args.size_gb * (1024**3))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plans = []
    if args.format in {"csv", "both"}:
        plans.append(
            (
                "csv",
                args.output_dir / "large_10gb.csv",
                args.output_dir / "large_10gb_schema.json",
                args.output_dir / "large_10gb_csv_manifest.json",
            )
        )
    if args.format in {"ndjson", "both"}:
        plans.append(
            (
                "ndjson",
                args.output_dir / "large_10gb.ndjson",
                args.output_dir / "large_10gb_ndjson_schema.json",
                args.output_dir / "large_10gb_ndjson_manifest.json",
            )
        )

    for fmt, output_path, schema_path, manifest_path in plans:
        print(f"\nGenerating {fmt.upper()} dataset")
        print(f"  output : {output_path}")
        print(f"  schema : {schema_path}")
        print(f"  target : {args.size_gb:.2f} GB")
        summary = generate_dataset(
            output_path,
            schema_path,
            manifest_path,
            fmt=fmt,
            target_bytes=target_bytes,
            error_every=args.error_every,
            buffer_rows=args.buffer_rows,
            seed=args.seed,
        )
        print(
            f"  done   : rows={summary['rows_written']:,}, "
            f"size={bytes_to_gb(summary['actual_size_bytes']):.2f} GB, "
            f"errors={sum(summary['error_counts'].values())}"
        )
        print(f"  manifest: {manifest_path}")


if __name__ == "__main__":
    main()
