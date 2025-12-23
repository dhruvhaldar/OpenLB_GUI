## 2024-05-24 - [Sidebar Memoization]
**Learning:** React.memo is effective for isolating sidebar navigation from high-frequency updates like terminal output or form typing.
**Action:** Extract static UI sections into memoized components when they share a parent with frequent state updaters.
