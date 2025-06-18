# Contributing to Biryani Battery Reminder

Thank you for your interest in contributing to Biryani Battery Reminder! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

-   **Python 3.13** (required as per project configuration) Although it should work with any version above 3.11
-   **Poetry** for dependency management
-   **Windows** (currently the only supported platform)
-   **Git** for version control

### Development Setup

1. **Fork and Clone the Repository**

    ```bash
    git clone https://github.com/YOUR_USERNAME/battery-reminder.git
    cd battery-reminder
    ```

2. **Install Dependencies**

    ```bash
    poetry install
    ```

3. **Run the Application**

    ```bash
    poetry run python -m battery_reminder
    ```

4. **Build the Executable** (for testing)
    ```bash
    poetry run python -m cx_Freeze
    ```

## 🛠️ Development Guidelines

### Code Style

-   **Formatting**: Use `ruff` for code formatting and linting

    ```bash
    poetry run ruff format .
    poetry run ruff check .
    ```

-   **Type Checking**: Use `pyright` for type checking
    ```bash
    poetry run pyright
    ```

### Project Structure

```
battery_reminder/
├── __main__.py          # Main entry point
├── src/                 # Source code modules
├── assets/              # Icons and resources
└── biryani_config.json  # Configuration file
```

### Key Dependencies

-   `desktop-notifier`: For system notifications
-   `batteryinfo`: For battery information
-   `pystray`: For system tray functionality
-   `ttkbootstrap`: For modern UI components
-   `psutil`: For system information

## 🐛 Reporting Bugs

Before reporting a bug:

1. Check if the issue has already been reported
2. Test with the latest version
3. Provide detailed information using the bug report template
4. Include system information and steps to reproduce

## 💡 Suggesting Features

When suggesting features:

1. Check if the feature has already been requested
2. Use the feature request template
3. Explain the use case and benefits
4. Consider if it fits the app's scope (battery monitoring and notifications)

## 🔧 Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

-   Follow the coding style guidelines
-   Add tests if applicable
-   Update documentation if needed
-   Test on Windows

### 3. Test Your Changes

-   Test the source code version
-   Test the executable build
-   Test battery notifications at different levels
-   Test system tray functionality

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add custom battery threshold settings"
```

Use conventional commit messages:

-   `feat:` for new features
-   `fix:` for bug fixes
-   `docs:` for documentation changes
-   `style:` for formatting changes
-   `refactor:` for code refactoring

### 5. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request using the provided template.

## 📋 Pull Request Guidelines

-   Use the provided pull request template
-   Ensure all checklist items are completed
-   Provide clear testing instructions
-   Include screenshots for UI changes
-   Link related issues if applicable

## 🧪 Testing

### Manual Testing Checklist

-   [ ] App starts without errors
-   [ ] System tray icon appears
-   [ ] Notifications work at low battery levels
-   [ ] Notifications work at full battery
-   [ ] Settings can be accessed and modified
-   [ ] App can be closed properly
-   [ ] Executable builds and runs correctly

### Automated Testing

Run the test suite:

```bash
poetry run pytest
```

## 📚 Documentation

-   Update docstrings for new functions
-   Update README.md if needed
-   Add comments for complex logic
-   Document any new configuration options

## 🤝 Code Review Process

1. All pull requests require review
2. Address review comments promptly
3. Maintainers may request changes
4. Once approved, changes will be merged

## 🎯 Project Goals

Biryani Battery Reminder aims to:

-   Provide fun, engaging battery notifications
-   Be lightweight and non-intrusive
-   Work reliably on Windows
-   Have a simple, user-friendly interface

## 📞 Getting Help

-   Open an issue for bugs or feature requests
-   Check existing issues and discussions
-   Be respectful and constructive in communications

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Biryani Battery Reminder! 🍛🔋
