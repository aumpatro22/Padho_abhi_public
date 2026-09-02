## 2024-06-22 - Sidebar Icon Buttons Accessibility
**Learning:** Found missing `aria-label`s on icon-only buttons (`X` and `Settings`) in the `Sidebar` component, making them inaccessible to screen readers since they have no text content.
**Action:** Always add descriptive `aria-label` attributes to any icon-only `<Button>` or `<button>` components (e.g., `aria-label="Close sidebar"`).

## 2024-11-20 - AuthPage Form Field Accessibility
**Learning:** Found multiple form inputs (`Input`) in `AuthPage.tsx` lacking `id` and `htmlFor` bindings to their corresponding `<label>` elements, plus missing `aria-label`s on the password visibility toggle and Neon Token input, severely reducing screen reader accessibility and clickable label area.
**Action:** Always bind `<label>` elements to their corresponding `<Input>` fields using explicit `htmlFor` and `id` attributes. Always add `aria-label` to icon-only toggle buttons and standalone inputs without visible labels.
