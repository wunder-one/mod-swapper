import unittest

from functions.update_progress import UpdateScanProgress


class UpdateScanProgressTests(unittest.TestCase):
    def test_default_ranges_match_previous_behavior(self):
        progress = UpdateScanProgress()

        self.assertEqual(progress.save_at(0, 10), 0.0)
        self.assertEqual(progress.save_at(5, 10), 0.025)
        self.assertEqual(progress.save_at(10, 10), 0.05)
        self.assertEqual(progress.prep, 0.05)
        self.assertEqual(progress.scan[0], 0.10)
        self.assertEqual(progress.scan_at(1, 10), 0.19)
        self.assertEqual(progress.scan_at(10, 10), 1.0)

    def test_in_phase_scales_manifest_fraction(self):
        progress = UpdateScanProgress(manifest=(0.0, 0.5))

        self.assertEqual(progress.in_phase(progress.manifest, 0.0), 0.0)
        self.assertEqual(progress.in_phase(progress.manifest, 0.5), 0.25)
        self.assertEqual(progress.in_phase(progress.manifest, 1.0), 0.5)

    def test_custom_ranges(self):
        progress = UpdateScanProgress(
            save=(0.25, 0.40),
            prep=0.40,
            scan=(0.40, 1.0),
        )

        self.assertEqual(progress.save_at(1, 2), 0.325)
        self.assertEqual(progress.prep, 0.40)
        self.assertEqual(progress.scan_at(1, 2), 0.70)


if __name__ == "__main__":
    unittest.main()
