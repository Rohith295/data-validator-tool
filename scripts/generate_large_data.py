"""Generate large CSV and NDJSON files with injected errors for testing."""

import json
import random
import sys
import time
from pathlib import Path

TARGET_DIR = Path("sample_data")
SEED = 42

# ~150 bytes per CSV row, ~200 bytes per NDJSON row
CSV_ROWS = 70_000_000   # ~10 GB
NDJSON_ROWS = 50_000_000  # ~10 GB

# inject an error roughly every 1M rows
ERROR_INTERVAL = 1_000_000

FIRST_NAMES = ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
LAST_NAMES = ["Smith", "Jones", "Brown", "Wilson", "Taylor", "Clark", "Hall", "Lee", "Young", "King"]
CITIES = ["Amsterdam", "London", "Berlin", "Paris", "Madrid", "Rome", "Vienna", "Oslo", "Dublin", "Zurich"]
COUNTRIES = ["NL", "UK", "DE", "FR", "ES", "IT", "AT", "NO", "IE", "CH"]


def make_row(i: int, rng: random.Random, inject_error: bool) -> dict:
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    city = rng.choice(CITIES)
    country = rng.choice(COUNTRIES)
    age = rng.randint(18, 80)
    salary = round(rng.uniform(30000, 120000), 2)
    email = f"{first.lower()}.{last.lower()}{i}@example.com"

    row = {
        "id": str(i),
        "first_name": first,
        "last_name": last,
        "email": email,
        "age": str(age),
        "salary": str(salary),
        "city": city,
        "country": country,
    }

    if inject_error:
        error_type = rng.randint(0, 4)
        if error_type == 0:
            row["email"] = ""  # non_empty
        elif error_type == 1:
            row["age"] = "not_a_number"  # types
        elif error_type == 2:
            row["age"] = str(rng.choice([-10, 200, 999]))  # range
        elif error_type == 3:
            row["first_name"] = ""  # non_empty
        elif error_type == 4:
            row["salary"] = "N/A"  # types
    return row


def generate_csv(path: Path, total_rows: int) -> None:
    rng = random.Random(SEED)
    headers = "id,first_name,last_name,email,age,salary,city,country\n"
    written = 0
    start = time.time()

    with open(path, "w", buffering=8 * 1024 * 1024) as f:
        f.write(headers)
        buf = []
        for i in range(1, total_rows + 1):
            inject = (i % ERROR_INTERVAL == 0)
            row = make_row(i, rng, inject)
            buf.append(",".join(row.values()))

            if len(buf) >= 100_000:
                f.write("\n".join(buf))
                f.write("\n")
                written += len(buf)
                buf.clear()
                if written % 5_000_000 == 0:
                    elapsed = time.time() - start
                    pct = written / total_rows * 100
                    size_gb = path.stat().st_size / (1024 ** 3)
                    print(f"  CSV: {written:>12,} rows ({pct:.0f}%) — {size_gb:.1f} GB — {elapsed:.0f}s")

        if buf:
            f.write("\n".join(buf))
            f.write("\n")

    size_gb = path.stat().st_size / (1024 ** 3)
    elapsed = time.time() - start
    print(f"  CSV done: {total_rows:,} rows, {size_gb:.1f} GB in {elapsed:.0f}s")


def generate_ndjson(path: Path, total_rows: int) -> None:
    rng = random.Random(SEED)
    written = 0
    start = time.time()

    with open(path, "w", buffering=8 * 1024 * 1024) as f:
        buf = []
        for i in range(1, total_rows + 1):
            inject = (i % ERROR_INTERVAL == 0)
            row = make_row(i, rng, inject)
            buf.append(json.dumps(row, separators=(",", ":")))

            if len(buf) >= 100_000:
                f.write("\n".join(buf))
                f.write("\n")
                written += len(buf)
                buf.clear()
                if written % 5_000_000 == 0:
                    elapsed = time.time() - start
                    pct = written / total_rows * 100
                    size_gb = path.stat().st_size / (1024 ** 3)
                    print(f"  NDJSON: {written:>12,} rows ({pct:.0f}%) — {size_gb:.1f} GB — {elapsed:.0f}s")

        if buf:
            f.write("\n".join(buf))
            f.write("\n")

    size_gb = path.stat().st_size / (1024 ** 3)
    elapsed = time.time() - start
    print(f"  NDJSON done: {total_rows:,} rows, {size_gb:.1f} GB in {elapsed:.0f}s")


if __name__ == "__main__":
    TARGET_DIR.mkdir(exist_ok=True)

    schema = {
        "validations": [
            {"columns_check": {"params": ["id", "first_name", "last_name", "email", "age", "salary", "city", "country"]}},
            {"non_empty_check": {"params": ["id", "first_name", "email"]}},
            {"types_check": {"params": {"age": "integer", "salary": "float"}}},
            {"range_check": {"params": {"age": {"min": 0, "max": 150}}}},
        ]
    }
    schema_path = TARGET_DIR / "large_schema.json"
    schema_path.write_text(json.dumps(schema, indent=2))
    print(f"Schema written to {schema_path}")

    fmt = sys.argv[1] if len(sys.argv) > 1 else "both"

    if fmt in ("csv", "both"):
        print(f"\nGenerating CSV ({CSV_ROWS:,} rows)...")
        generate_csv(TARGET_DIR / "large_10gb.csv", CSV_ROWS)

    if fmt in ("ndjson", "both"):
        print(f"\nGenerating NDJSON ({NDJSON_ROWS:,} rows)...")
        generate_ndjson(TARGET_DIR / "large_10gb.ndjson", NDJSON_ROWS)

    print("\nDone!")
