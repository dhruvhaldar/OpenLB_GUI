## 2024-05-24 - [Sidebar Memoization]
**Learning:** React.memo is effective for isolating sidebar navigation from high-frequency updates like terminal output or form typing.
**Action:** Extract static UI sections into memoized components when they share a parent with frequent state updaters.

## 2026-01-01 - [Memory Efficient Directory Scanning]
**Learning:** `glob.glob()` builds the entire list of matches in memory. When combining results from multiple glob patterns (e.g. searching different depths), using `+` operator on lists creates multiple intermediate lists.
**Action:** Use `glob.iglob()` (iterator) combined with `itertools.chain()` to lazily iterate over matches without allocating large lists, especially when the directory structure is potentially large.

## 2026-01-05 - [Optimized Directory Traversal]
**Learning:** In simulation environments where output files (e.g., thousands of VTK files) are often stored in the case root, naive directory recursion (`os.scandir`) for service discovery can be extremely slow. Assuming a "Case implies Leaf" structure allows for skipping massive subtrees.
**Action:** Identify domain-specific structural constraints (like "Projects don't contain other Projects") and use explicit `continue` or `return` in traversal loops to prune search paths early.

## 2026-01-20 - [Efficient Case Duplication]
**Learning:** Simulation cases often accumulate massive build artifacts (`.o`) and output files (`.vtk`). Naively using `shutil.copytree` duplicates gigabytes of redundant data, causing I/O bottlenecks.
**Action:** Use `shutil.ignore_patterns` with domain-specific extensions (`*.vtk`, `*.o`, `tmp`) to exclude artifacts during duplication, transforming O(GB) operations into O(KB).

## 2024-05-24 - [Subprocess Polling Latency]
**Learning:** Polling subprocesses with `process.poll()` and `time.sleep()` introduces unconditional latency equal to the sleep interval, even for instant commands. `process.wait(timeout=...)` blocks *up to* the timeout but returns immediately on completion.
**Action:** Replace `sleep`-based polling loops with `wait(timeout)` loops to reduce execution latency for short-lived processes (e.g. `make` checks) while maintaining timeouts and output monitoring.

## 2024-05-24 - [List Reconciliation Optimization]
**Learning:** Even with `React.memo` on list items, the parent component still performs O(N) work to reconcile the list container (creating VDOM nodes for each item) on every render. This impacts responsiveness of controlled inputs (like search filters) in the same component.
**Action:** Extract the list mapping logic into a separate, memoized container component. This stops React reconciliation at the container level when the list data hasn't changed, turning O(N) work into O(1) during input typing.

## 2026-01-25 - [O(1) DOM List Navigation]
**Learning:** Using `querySelectorAll` in keyboard event handlers forces the browser to scan the entire subtree on every keypress, creating O(N) latency that is noticeable in large lists.
**Action:** Replace subtree queries with O(1) DOM traversal properties like `closest`, `nextElementSibling`, and `previousElementSibling` for keyboard navigation in virtual or long lists.

## 2026-05-21 - [Optimized Ignore Patterns]
**Learning:** `shutil.ignore_patterns` uses `fnmatch` inside a loop, creating O(N*M) complexity where N is files and M is patterns. For directories with thousands of files (e.g. simulation outputs), this is significantly slower than O(N) set lookups and `str.endswith`.
**Action:** Replace `shutil.ignore_patterns` with a custom callback using `set` (for exact matches) and `tuple` (for `endswith` extensions) when performance is critical.
