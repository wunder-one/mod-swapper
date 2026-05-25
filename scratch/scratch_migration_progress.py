"""Scratch test — preview the migration progress dialog.

Run from repo root:
    python scratch/scratch_migration_progress.py

Imports ui/migration_progress.py directly so you can iterate on it.
Auto-closes after ~5 s.
"""

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import customtkinter

from ui.migration_progress import MigrationProgress

customtkinter.set_default_color_theme(str(_REPO_ROOT / "ui" / "theme.json"))

root = customtkinter.CTk()
root.withdraw()

simulate_profiles = 50
step = 0

dialog = MigrationProgress(root)


def simulate():
    dialog.set_total_profiles(simulate_profiles)
    root.after(800, dialog_update_progress)


def dialog_update_progress():
    global step
    dialog.update_progress(step)
    step += 1
    if step < simulate_profiles:
        dialog.set_status(f"Processing profile {step}...")
        root.after(800, dialog_update_progress)
    else:
        dialog.update_progress(simulate_profiles)
        dialog.set_status("Migration complete!")
        root.after(600, cleanup)


def cleanup():
    dialog.destroy()
    root.deiconify()
    root.title("Done — close this window")
    x = root.winfo_screenwidth() // 2 - root.winfo_width() // 2
    y = root.winfo_screenheight() // 2 - root.winfo_height() // 2
    root.geometry(f"300x100+{x}+{y}")
    customtkinter.CTkLabel(root, text="Test finished.").pack(expand=True, fill="both")
    root.after(2000, root.destroy)


root.after(500, simulate)
root.mainloop()
