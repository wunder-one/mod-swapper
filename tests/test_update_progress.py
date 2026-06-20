from functions.update_progress import UpdateScanProgress


def test_default_ranges():
    progress = UpdateScanProgress()

    assert progress.save_at(0, 10) == 0.0
    assert progress.save_at(5, 10) == 0.325
    assert progress.save_at(10, 10) == 0.65
    assert progress.prep == 0.65
    assert progress.scan[0] == 0.70
    assert progress.scan_at(1, 10) == 0.73
    assert progress.scan_at(10, 10) == 1.0


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
