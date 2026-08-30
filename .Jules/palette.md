## 2024-05-18 - Missing ARIA Labels on Icon Buttons
**Learning:** Icon-only buttons (like the password toggle, toast close button, and chat send button) in this app's components frequently lack `aria-label` attributes, making them inaccessible to screen reader users.
**Action:** Add descriptive `aria-label` attributes to these components to improve accessibility without changing the visual layout.
