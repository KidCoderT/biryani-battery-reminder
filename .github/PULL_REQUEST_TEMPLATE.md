---
name: Code Contribution
about: Submit a code change to Biryani Battery Reminder
title: "[TYPE] Concise description of the change"
labels: ""
assignees: ""
---

**Fixes # (issue number)**: If this PR fixes an issue, please add "Fixes #123" (replace 123 with the actual issue number) to automatically close the issue when merged.

**Changes Proposed:**
Describe the changes you've made in this pull request. Be clear and concise.

-   List individual changes (e.g., "Added custom battery threshold settings", "Fixed notification not showing on Windows 11")
-   Explain _why_ these changes were made.

**Checklist (Please check all that apply):**

-   [ ] I have read the project's contribution guidelines.
-   [ ] My code follows the project's coding style (using ruff for formatting).
-   [ ] I have tested my changes on Windows (the current supported platform).
-   [ ] I have updated documentation if necessary (README, docstrings, etc.).
-   [ ] I have tested both the executable build and source code versions.
-   [ ] My changes don't break existing functionality (notifications, system tray, etc.).

**Testing Instructions:**
Provide clear steps on how to review and test your changes locally.

1. **For Source Code Testing:**

    - Clone the repository
    - Install dependencies: `poetry install`
    - Run the app: `poetry run python -m battery_reminder`

2. **For Executable Testing:**

    - Build the executable: `poetry run python -m cx_Freeze`
    - Test the generated .exe file

3. **Specific Test Cases:**
    - Test battery notifications at different levels
    - Test system tray functionality
    - Test app startup and shutdown
    - Test on different Windows versions if possible

**Screenshots/GIFs (if applicable):**
Add any relevant screenshots or GIFs that demonstrate your changes, especially for UI modifications.

**System Information:**

-   OS: [e.g. Windows 10, Windows 11]
-   Python Version: [e.g. 3.13]
-   Installation Method: [Source code / Executable]

**Further Comments:**
Add any additional context, notes, or considerations here. For example:

-   Any breaking changes that users should be aware of
-   Performance implications
-   Dependencies added or removed
