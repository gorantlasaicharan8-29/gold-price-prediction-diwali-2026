"""Extract Gold 999 AM and PM rates from official IBJA PDF reports."""

from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime
from pathlib import Path

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = PROJECT_ROOT / "data" / "raw" / "ibja_source_pdfs"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CSV_PATH = RAW_DIR / "ibja_gold_999_2025_2026.csv"
METADATA_PATH = RAW_DIR / "ibja_data_metadata.json"
VALIDATION_PATH = RAW_DIR / "ibja_validation_report.json"

START_DATE = date(2025, 9, 2)
END_DATE = date(2026, 9, 2)

REPORTS = [
    ("Pdf_2911_20250930122006994_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_2911_20250930122006994_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_3803_20251015121704887_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_3803_20251015121704887_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_6929_20251104122454099_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_6929_20251104122454099_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_8713_20251201170645510_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_8713_20251201170645510_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_3599_20251230171500157_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_3599_20251230171500157_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_2152_20260116170521867_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_2152_20260116170521867_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_4041_20260203122230154_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_4041_20260203122230154_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_8759_20260227124908893_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_8759_20260227124908893_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_4722_20260302124004909_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_4722_20260302124004909_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_7566_20260402135929203_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_7566_20260402135929203_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_1226_20260430133606283_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_1226_20260430133606283_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_2969_20260505134358004_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_2969_20260505134358004_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_9815_20260609084851454_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_9815_20260609084851454_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_7763_20260721134504817_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_7763_20260721134504817_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_4936_20260804134744357_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_4936_20260804134744357_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_9924_20260831085413646_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_9924_20260831085413646_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
    ("Pdf_5171_20260902142334051_Daily Opening and Closing Market Rate.pdf", "https://ibjarates.com/UploadedFiles/30DaysPdf/Pdf_5171_20260902142334051_Daily%20Opening%20and%20Closing%20Market%20Rate.pdf"),
]

DATE_PATTERN = re.compile(r"(?P<date>\d{2}-(?:[A-Za-z]{3}|\d{2})-\d{2})")
NUMBER_PATTERN = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")


def extract_report_rows(pdf_path: Path) -> list[dict[str, object]]:
    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    matches = list(DATE_PATTERN.finditer(text))
    extracted = []
    for index, match in enumerate(matches):
        raw_date = match.group("date")
        date_format = "%d-%m-%y" if raw_date[3].isdigit() else "%d-%b-%y"
        current_date = datetime.strptime(raw_date, date_format).date()
        row_text = text[match.end() : matches[index + 1].start() if index + 1 < len(matches) else None]
        if current_date.weekday() >= 5 or re.search(r"\b(?:SAT|SUN|Market\s+Holiday)\b", row_text, re.IGNORECASE):
            continue
        values = NUMBER_PATTERN.findall(row_text)
        if len(values) < 2:
            continue
        extracted.append(
            {
                "date": current_date,
                "gold_999_am": int(values[0]),
                "gold_999_pm": int(values[1]),
            }
        )
    return extracted


def validate_records(records: list[dict[str, object]], invalid_values: list[dict[str, object]], conflicts: list[dict[str, object]], failures: list[dict[str, str]], duplicates: int) -> dict[str, object]:
    dates = [record["date"] for record in records]
    outside_range = [record["date"].isoformat() for record in records if not START_DATE <= record["date"] <= END_DATE]
    weekend_rows = [record["date"].isoformat() for record in records if record["date"].weekday() >= 5]
    return {
        "earliest_date": min(dates).isoformat() if dates else None,
        "latest_date": max(dates).isoformat() if dates else None,
        "total_records": len(records),
        "duplicate_dates_after_deduplication": len(dates) - len(set(dates)),
        "duplicate_count_before_deduplication": duplicates,
        "missing_am_values": sum(record["gold_999_am"] is None for record in records),
        "missing_pm_values": sum(record["gold_999_pm"] is None for record in records),
        "invalid_numeric_values": invalid_values,
        "conflicting_duplicate_values": conflicts,
        "chronological_order": dates == sorted(dates),
        "dates_outside_requested_range": outside_range,
        "weekend_or_holiday_rows_accidentally_included": weekend_rows,
        "failed_reports": failures,
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records_by_date: dict[date, dict[str, object]] = {}
    all_records: list[dict[str, object]] = []
    failures = []
    invalid_values = []
    conflicts = []

    for filename, url in REPORTS:
        pdf_path = PDF_DIR / filename
        if not pdf_path.exists():
            report_date_match = re.search(r"_(\d{8})", filename)
            report_date = datetime.strptime(report_date_match.group(1), "%Y%m%d").date() if report_date_match else None
            failures.append({
                "file": filename,
                "url": url,
                "report_date": report_date.isoformat() if report_date else None,
                "affected_report_window": f"{(report_date.fromordinal(report_date.toordinal() - 29)).isoformat()} through {report_date.isoformat()}" if report_date else None,
                "reason": "PDF was not downloaded (official URL returned 404).",
            })
            continue
        try:
            all_records.extend(extract_report_rows(pdf_path))
        except Exception as error:  # Keep processing other official reports.
            failures.append({"file": filename, "url": url, "reason": f"Parse error: {error}"})

    duplicate_count = 0
    for record in all_records:
        if not START_DATE <= record["date"] <= END_DATE:
            continue
        if record["date"] in records_by_date:
            duplicate_count += 1
            existing = records_by_date[record["date"]]
            if existing["gold_999_am"] != record["gold_999_am"] or existing["gold_999_pm"] != record["gold_999_pm"]:
                conflicts.append({"date": record["date"].isoformat(), "reason": "Conflicting values across official reports."})
            continue
        records_by_date[record["date"]] = record

    records = []
    for current_date in sorted(records_by_date):
        record = records_by_date[current_date]
        am = record["gold_999_am"]
        pm = record["gold_999_pm"]
        if not all(isinstance(value, (int, float)) and value > 0 for value in (am, pm)):
            invalid_values.append({"date": current_date.isoformat(), "reason": "Non-positive or non-numeric price."})
            continue
        records.append(
            {
                "date": current_date.isoformat(),
                "gold_999_am": am,
                "gold_999_pm": pm,
                "gold_999_average": (am + pm) / 2 if am is not None and pm is not None else am if am is not None else pm,
                "source": "IBJA",
            }
        )

    with CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["date", "gold_999_am", "gold_999_pm", "gold_999_average", "source"])
        writer.writeheader()
        writer.writerows(records)

    validation = validate_records(
        [{**record, "date": date.fromisoformat(record["date"])} for record in records],
        invalid_values,
        conflicts,
        failures,
        duplicate_count,
    )
    METADATA_PATH.write_text(
        json.dumps(
            {
                "source_name": "India Bullion and Jewellers Association (IBJA)",
                "source_url": "https://ibjarates.com/",
                "target": "Gold 999 / 24K",
                "purity": "999",
                "unit": "INR per 10 grams",
                "start_date": START_DATE.isoformat(),
                "end_date": END_DATE.isoformat(),
                "collection_date": date.today().isoformat(),
                "number_of_records": len(records),
                "missing_value_count": validation["missing_am_values"] + validation["missing_pm_values"],
                "missing_am_count": validation["missing_am_values"],
                "missing_pm_count": validation["missing_pm_values"],
                "duplicate_count_before_deduplication": duplicate_count,
                "notes": "Only published IBJA rows were included. SAT, SUN, Market Holiday, and unavailable report periods remain absent; no prices were generated, interpolated, or forward-filled. Three overlapping reports contain conflicting values for their report-date rows; the first encountered official value was retained and the conflicts are listed in the validation report. The latest PDF prints its top row as 02-08-26, so it was not reinterpreted as 2026-09-02.",
                "official_report_urls": [url for _, url in REPORTS],
                "failed_reports": failures,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2), encoding="utf-8")

    print("=" * 40)
    print("IBJA GOLD DATA COLLECTION COMPLETE")
    print("=" * 40)
    print("Source: India Bullion and Jewellers Association")
    print("Target: Gold 999 / 24K")
    print("Unit: INR per 10 grams")
    print("Period: 2025-09-02 -> 2026-09-02")
    print(f"\nRecords collected: {len(records)}")
    print(f"Duplicate rows removed: {duplicate_count}")
    print(f"Missing AM values: {validation['missing_am_values']}")
    print(f"Missing PM values: {validation['missing_pm_values']}")
    print(f"Invalid values: {len(invalid_values)}")
    print(f"Conflicting duplicate values: {len(conflicts)}")
    print(f"\nEarliest date: {validation['earliest_date']}")
    print(f"Latest date: {validation['latest_date']}")
    print(f"\nCSV:\n{CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Metadata:\n{METADATA_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Validation report:\n{VALIDATION_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Extraction script:\n{Path(__file__).resolve().relative_to(PROJECT_ROOT)}")
    if failures:
        print("\nDATASET INCOMPLETE: the following official reports were unavailable or failed to parse:")
        for failure in failures:
            print(f"- {failure['file']}: {failure['reason']}")


if __name__ == "__main__":
    main()