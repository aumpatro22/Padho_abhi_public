## 2024-06-22 - Sidebar Icon Buttons Accessibility
**Learning:** Found missing `aria-label`s on icon-only buttons (`X` and `Settings`) in the `Sidebar` component, making them inaccessible to screen readers since they have no text content.
**Action:** Always add descriptive `aria-label` attributes to any icon-only `<Button>` or `<button>` components (e.g., `aria-label="Close sidebar"`).

## 2026-08-25 - Password Toggle Accessibility
**Learning:** Interactive icon-only buttons like password toggles lack context for screen readers and often miss proper keyboard focus indicators, making them hard to use for a11y users.
**Action:** Always add `aria-label`, `aria-pressed`, and `focus-visible` classes to icon-only toggle buttons to ensure they are accessible to both screen readers and keyboard users.
