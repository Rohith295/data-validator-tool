#!/usr/bin/env bash
#
# Runs data-validate against all sample data files with their matching schemas.
# Usage: ./run_samples.sh
#        ./run_samples.sh --report    (also generate HTML reports)

set -euo pipefail

EXTRA_FLAGS="${*:-}"

echo "========================================="
echo " data-validator — sample data run"
echo "========================================="
echo ""

run_validation() {
    local file="$1"
    local schema="$2"
    local label
    label=$(basename "$file")

    printf "%-40s " "$label"
    if python -m data_validator --file_path "$file" --schema_path "$schema" -q $EXTRA_FLAGS 2>/dev/null; then
        echo "PASS"
    else
        code=$?
        if [ "$code" -eq 1 ]; then
            echo "FAIL"
        else
            echo "ERROR (exit $code)"
        fi
    fi
}

# Small assessment CSVs (1-4) with my_schema.json
for i in 1 2 3 4; do
    if [ -f "sample_data/${i}.csv" ]; then
        run_validation "sample_data/${i}.csv" "sample_data/my_schema.json"
    fi
done

# Small JSONL test file with customers schema
if [ -f "sample_data/test_small.jsonl" ]; then
    run_validation "sample_data/test_small.jsonl" "sample_data/customers_schema.json"
fi

# 2M row CSV
if [ -f "sample_data/customers-2000000.csv" ]; then
    echo ""
    echo "--- Large files (may take a moment) ---"
    echo ""
    time run_validation "sample_data/customers-2000000.csv" "sample_data/customers_schema.json"
fi

# 5M row JSONL
if [ -f "sample_data/customers-5m.jsonl" ]; then
    time run_validation "sample_data/customers-5m.jsonl" "sample_data/customers_5m_schema.json"
fi

# 10M row CSV
if [ -f "sample_data/customers-10m.csv" ]; then
    time run_validation "sample_data/customers-10m.csv" "sample_data/customers_10m_schema.json"
fi

echo ""
echo "Done."
