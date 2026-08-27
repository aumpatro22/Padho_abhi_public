## 2024-06-22 - Sidebar Icon Buttons Accessibility
**Learning:** Found missing `aria-label`s on icon-only buttons (`X` and `Settings`) in the `Sidebar` component, making them inaccessible to screen readers since they have no text content.
**Action:** Always add descriptive `aria-label` attributes to any icon-only `<Button>` or `<button>` components (e.g., `aria-label="Close sidebar"`).

## 2026-08-27 - Form Input Label Association
**Learning:** Found multiple instances where `<label>` tags lacked a `htmlFor` attribute linking to an `id` on their corresponding `<Input>` or `<Textarea>` (e.g., in `SyllabusUploadModal` and `SettingsTab`). This breaks click-to-focus behavior and impairs screen reader accessibility.
**Action:** Always link `<label>` elements to their corresponding form inputs by adding an `id` on the input and matching it with the `htmlFor` attribute on the label.
