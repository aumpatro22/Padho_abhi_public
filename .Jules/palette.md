## 2024-06-22 - Sidebar Icon Buttons Accessibility
**Learning:** Found missing `aria-label`s on icon-only buttons (`X` and `Settings`) in the `Sidebar` component, making them inaccessible to screen readers since they have no text content.
**Action:** Always add descriptive `aria-label` attributes to any icon-only `<Button>` or `<button>` components (e.g., `aria-label="Close sidebar"`).

## 2026-09-04 - Utility Icon Buttons Accessibility
**Learning:** Found multiple instances of icon-only buttons (theme toggle, show/hide password, dismiss toast, send message) lacking `aria-label` attributes, creating an accessibility barrier for screen reader users.
**Action:** Add dynamic or static `aria-label`s to utility buttons that only use icons (e.g. `aria-label={showPassword ? "Hide password" : "Show password"}`) across all components.
