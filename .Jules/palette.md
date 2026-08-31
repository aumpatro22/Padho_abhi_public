## 2024-06-22 - Sidebar Icon Buttons Accessibility
**Learning:** Found missing `aria-label`s on icon-only buttons (`X` and `Settings`) in the `Sidebar` component, making them inaccessible to screen readers since they have no text content.
**Action:** Always add descriptive `aria-label` attributes to any icon-only `<Button>` or `<button>` components (e.g., `aria-label="Close sidebar"`).
## 2024-09-02 - Icon-Only Button Accessibility Pattern
**Learning:** Found multiple instances where the custom `<Button>` component with `size="icon"` was missing `aria-label` attributes. This pattern prevents screen reader users from understanding the purpose of interactive elements like theme toggles, sidebar menus, and form submission buttons when they lack visible text.
**Action:** Always verify that `<Button size="icon">` (or any icon-only interactive element) explicitly includes a descriptive `aria-label` attribute during component implementation or review.
