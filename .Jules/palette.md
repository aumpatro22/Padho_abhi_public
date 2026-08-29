## 2025-05-18 - Missing ARIA Labels on Icon Buttons
**Learning:** Icon-only buttons without `aria-label` attributes are a common accessibility issue in this codebase, particularly in custom components like `Toast`, `AuthPage` toggles, and floating action buttons.
**Action:** Proactively check all new and existing icon-only buttons for descriptive `aria-label` attributes to ensure screen reader compatibility.
