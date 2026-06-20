from functions.update_progress import UpdateScanProgress


def test_in_phase_scales_manifest_fraction():
    progress = UpdateScanProgress(manifest=(0.0, 0.5))

    assert progress.in_phase(progress.manifest, 0.0) == 0.0
    assert progress.in_phase(progress.manifest, 0.5) == 0.25
    assert progress.in_phase(progress.manifest, 1.0) == 0.5


def test_custom_ranges():
    progress = UpdateScanProgress(
        save=(0.25, 0.40),
        prep=0.40,
        scan=(0.40, 1.0),
    )

    assert progress.save_at(1, 2) == 0.325
    assert progress.prep == 0.40
    assert progress.scan_at(1, 2) == 0.70
