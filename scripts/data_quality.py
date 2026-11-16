
import pandas as pd


def check_required_columns(df, required_columns):
    """Check whether all required columns exist."""

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    return {
        "check": "required_columns",
        "passed": len(missing) == 0,
        "details": f"Missing columns: {missing}"
    }


def check_null_values(df, columns):
    """Check for null values in selected columns."""

    results = {}

    for column in columns:
        if column not in df.columns:
            results[column] = "COLUMN_NOT_FOUND"
        else:
            results[column] = int(df[column].isnull().sum())

    passed = all(value == 0 for value in results.values())

    return {
        "check": "null_values",
        "passed": passed,
        "details": results
    }


def check_duplicates(df, key_columns):
    """Check duplicate records using business key columns."""

    missing = [
        column for column in key_columns
        if column not in df.columns
    ]

    if missing:
        return {
            "check": "duplicates",
            "passed": False,
            "details": f"Missing key columns: {missing}"
        }

    duplicate_count = int(
        df.duplicated(subset=key_columns).sum()
    )

    return {
        "check": "duplicates",
        "passed": duplicate_count == 0,
        "details": {
            "duplicate_count": duplicate_count,
            "key_columns": key_columns
        }
    }


def check_non_negative(df, columns):
    """Check that numeric measurements are non-negative."""

    results = {}

    for column in columns:
        if column not in df.columns:
            results[column] = "COLUMN_NOT_FOUND"
        else:
            invalid_count = int((df[column] < 0).sum())
            results[column] = invalid_count

    passed = all(value == 0 for value in results.values())

    return {
        "check": "non_negative_values",
        "passed": passed,
        "details": results
    }


def check_relationships(
    child_df,
    child_column,
    parent_df,
    parent_column
):
    """Check that child keys exist in the parent dataset."""

    if child_column not in child_df.columns:
        return {
            "check": "relationships",
            "passed": False,
            "details": f"Missing child column: {child_column}"
        }

    if parent_column not in parent_df.columns:
        return {
            "check": "relationships",
            "passed": False,
            "details": f"Missing parent column: {parent_column}"
        }

    valid_keys = set(parent_df[parent_column].dropna())

    invalid_count = int(
        (
            child_df[child_column].notna()
            & ~child_df[child_column].isin(valid_keys)
        ).sum()
    )

    return {
        "check": "relationships",
        "passed": invalid_count == 0,
        "details": {
            "invalid_relationships": invalid_count
        }
    }


def print_quality_report(results):
    """Display a readable data quality report."""

    print("\nDATA QUALITY REPORT")
    print("=" * 45)

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        print(f"\nCheck: {result['check']}")
        print(f"Status: {status}")
        print(f"Details: {result['details']}")

    overall = all(result["passed"] for result in results)

    print("\n" + "=" * 45)
    print(f"OVERALL RESULT: {'PASS' if overall else 'FAIL'}")

    return overall
