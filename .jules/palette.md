# Palette's Journal

## 2025-10-26 - [Discoverable Case Paths]
**Learning:** Users need to reference file paths frequently in simulation workflows, but the UI presents them as static text. Making these paths interactive (copyable) reduces friction and errors in command-line operations.
**Action:** When displaying file system paths, always consider adding a "Copy to Clipboard" action nearby, especially in developer-focused tools.

## 2025-02-19 - [Stable UI Shells]
**Learning:** Replacing an entire section of the UI with a generic loader causes layout shifts and disorienting context loss (e.g., the section header disappearing).
**Action:** Always maintain the "UI Shell" (headers, toolbars) during loading states. Render the loader *inside* the content area, disabling interactive elements in the shell rather than removing them. This makes the application feel more stable and responsive.
