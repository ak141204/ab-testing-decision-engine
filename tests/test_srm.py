import pandas as pd

from srm import check_srm, diagnose_srm_by_segment, full_srm_report


def make_groups(control_n, treatment_n):
    return pd.DataFrame({
        "group": (
            ["control"] * control_n
            + ["treatment"] * treatment_n
        )
    })


def test_balanced_50_50_allocation_passes():
    df = make_groups(5000, 5000)

    result = check_srm(df)

    assert result.srm_detected == False
    assert result.observed_split == 0.5
    assert result.observed_control_n == 5000
    assert result.observed_treatment_n == 5000


def test_strongly_imbalanced_allocation_detects_srm():
    df = make_groups(3000, 7000)

    result = check_srm(df)

    assert result.srm_detected == True
    assert result.observed_split == 0.7
    assert result.p_value < 0.001


def test_custom_expected_split_is_supported():
    df = make_groups(3000, 7000)

    result = check_srm(df, expected_split=0.7)

    assert result.srm_detected == False
    assert result.expected_split == 0.7
    assert result.observed_split == 0.7


def make_segmented_data():
    records = []

    # iOS: intentionally imbalanced 30/70
    records.extend(
        {"platform": "iOS", "group": "control"}
        for _ in range(300)
    )
    records.extend(
        {"platform": "iOS", "group": "treatment"}
        for _ in range(700)
    )

    # Android: balanced 50/50
    for platform in ["Android", "Web"]:
        records.extend(
            {"platform": platform, "group": "control"}
            for _ in range(500)
        )
        records.extend(
            {"platform": platform, "group": "treatment"}
            for _ in range(500)
        )

    return pd.DataFrame(records)


def test_segment_diagnosis_identifies_imbalanced_platform():
    df = make_segmented_data()

    results = diagnose_srm_by_segment(df, ["platform"])

    diagnoses = {
        result.segment_value: result
        for result in results
    }

    assert diagnoses["iOS"].flagged == True
    assert diagnoses["Android"].flagged == False
    assert diagnoses["Web"].flagged == False


def test_full_report_includes_segments_when_overall_srm_detected():
    df = make_segmented_data()

    report = full_srm_report(df, ["platform"])

    assert report["overall"].srm_detected == True
    assert len(report["segments"]) == 3


def test_full_report_skips_segment_diagnosis_when_clean():
    df = make_groups(5000, 5000)
    df["platform"] = "iOS"

    report = full_srm_report(df, ["platform"])

    assert report["overall"].srm_detected == False
    assert report["segments"] == []
