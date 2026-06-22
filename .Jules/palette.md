## 2024-06-22 - Sidebar Icon Buttons Accessibility
**Learning:** Found missing `aria-label`s on icon-only buttons (`X` and `Settings`) in the `Sidebar` component, making them inaccessible to screen readers since they have no text content.
**Action:** Always add descriptive `aria-label` attributes to any icon-only `<Button>` or `<button>` components (e.g., `aria-label="Close sidebar"`).
