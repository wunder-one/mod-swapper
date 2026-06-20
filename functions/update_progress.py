from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateScanProgress:
    """Bar fill ranges (0.0–1.0) for the update scan dialog, step 1.
    
    The progress bar is divided into four phases:
    - manifest: the progress of the manifest update
    - save: the progress of the save file update
    - prep: the progress of the preparation for the update (single tick)
    - scan: the progress of the scan for the update

    1.0 = 100%
    """

    manifest: tuple[float, float] = (0.0, 1.0)
    save: tuple[float, float] = (0.0, 0.65)
    prep: float = 0.65
    scan: tuple[float, float] = (0.70, 1.0)

    def in_phase(self, phase: tuple[float, float], fraction: float) -> float:
        start, end = phase
        return start + (end - start) * fraction

    def save_at(self, index: int, total: int) -> float:
        fraction = index / total if total else 1.0
        return self.in_phase(self.save, fraction)

    def scan_at(self, index: int, total: int) -> float:
        fraction = index / total if total else 1.0
        return self.in_phase(self.scan, fraction)


DEFAULT_UPDATE_SCAN_PROGRESS = UpdateScanProgress()
