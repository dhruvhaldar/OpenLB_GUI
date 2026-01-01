## 2024-05-24 - [Sidebar Memoization]
**Learning:** React.memo is effective for isolating sidebar navigation from high-frequency updates like terminal output or form typing.
**Action:** Extract static UI sections into memoized components when they share a parent with frequent state updaters.

## 2026-01-01 - [Memory Efficient Directory Scanning]
**Learning:** `glob.glob()` builds the entire list of matches in memory. When combining results from multiple glob patterns (e.g. searching different depths), using `+` operator on lists creates multiple intermediate lists.
**Action:** Use `glob.iglob()` (iterator) combined with `itertools.chain()` to lazily iterate over matches without allocating large lists, especially when the directory structure is potentially large.
