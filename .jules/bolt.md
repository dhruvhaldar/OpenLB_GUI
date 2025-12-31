## 2024-02-14 - Atomic File Read Optimization
**Learning:** `os.path.getsize` followed by `open()` is a common anti-pattern that introduces a race condition (TOCTOU) and an extra system call. Using `os.fstat(f.fileno())` on an open file descriptor is safer and faster because it uses the already open handle.
**Action:** When enforcing file size limits, always open the file first and use `fstat` on the descriptor instead of checking the path beforehand.
