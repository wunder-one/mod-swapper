from pathlib import Path

# set up a test file and an existing directory
src = Path(r"C:\Users\wes\Desktop\test-source\test.txt")
src.write_text("hello")

dst = Path(r"C:\Users\wes\Desktop\test-dest\test.txt")
# dst.mkdir()

src.copy(dst)  # what happens?