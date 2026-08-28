## 2024-06-22 - Sidebar Icon Buttons Accessibility
**Learning:** Found missing `aria-label`s on icon-only buttons (`X` and `Settings`) in the `Sidebar` component, making them inaccessible to screen readers since they have no text content.
**Action:** Always add descriptive `aria-label` attributes to any icon-only `<Button>` or `<button>` components (e.g., `aria-label="Close sidebar"`).
## 2024-08-01 - Widespread Icon Buttons Accessibility
**Learning:** Found several other missing `aria-label`s on icon-only buttons (`Moon`, `Sun`, `Menu`, `X`, `Eye`, `EyeOff`) across multiple components (`App`, `MobileBottomNav`, `Toast`, `AuthPage`), confirming a pattern of accessibility issues.
**Action:** Consistently audit and add `aria-label` attributes to any interactive elements that rely solely on icons to convey meaning.
