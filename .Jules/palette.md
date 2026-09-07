## 2024-06-22 - Sidebar Icon Buttons Accessibility
**Learning:** Found missing `aria-label`s on icon-only buttons (`X` and `Settings`) in the `Sidebar` component, making them inaccessible to screen readers since they have no text content.
**Action:** Always add descriptive `aria-label` attributes to any icon-only `<Button>` or `<button>` components (e.g., `aria-label="Close sidebar"`).

## 2026-09-07 - Missing ARIA labels on Icon-Only Buttons
**Learning:** Discovered a pattern across the app where custom icon-only components (hamburger menus, theme toggles, close buttons, password visibility toggles) lacked `aria-label` attributes, impacting screen reader accessibility.
**Action:** Add `aria-label`s to all icon-only interactive elements as part of standard component creation and review processes.
