# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

**Biryani Battery Reminder** — a Windows-only desktop tray app (Python 3.13) that monitors
laptop battery, fires fun emoji desktop notifications for low/high/overflow charge, and
auto-switches the Windows power plan to Power Saver when low (restoring it later). UI is a
ttkbootstrap settings window; it lives in the system tray. Distributed as a cx_Freeze exe
wrapped in an Inno Setup installer.

## Commands

```bash
uv sync --extra windows                     # install deps (including pywin32)
uv run python -m battery_reminder           # run the app
uv run python build.py build                # build the frozen exe (cx_Freeze) -> build/exe.win-amd64-3.13/
uv run ruff format . && uv run ruff check . # format + lint
uv run pyright                              # type check
```
Then compile `Inno-Setup.iss` with Inno Setup to produce the installer.

> Note: `uv run pytest` is documented in CONTRIBUTING.md but the files in `tests/` are
> interactive manual scripts, not pytest tests, and are stale vs current code — they will
> not pass. There is no working automated test suite.

## Architecture

Two-process design coordinated from `battery_reminder/__main__.py` (`App` class):

- **Main process**: Tk/ttkbootstrap GUI (`src/settings_gui.py`), pystray tray icon (own
  thread), and the **Notifier** (`src/notifier.py`) running in its own thread with a private
  asyncio loop. Notifier consumes two `multiprocessing.Queue`s (normal + critical) and shows
  desktop notifications via `desktop_notifier`, plays `.wav` sounds via `nava`.
- **Background process** (`src/background_proc.py`, `multiprocessing.Process`): polls the
  battery every 1s (`batteryinfo`), decides which notification to enqueue, and drives the
  power-plan switching (`src/powerplan.py`, shells out to `powercfg`).
- **IPC**: the two queues + three `multiprocessing.Value(c_bool)` flags
  (`stop_bg_process_flag`, `settings_updated_flag`, `powerplan_restarted_flag`) polled by the
  bg loop.

Support modules: `src/app_config_manager.py` (JSON config load/save with default-merge +
self-heal; `AppConfig` TypedDict), `src/startup_manager.py` (Startup-folder .lnk via
win32com), `src/assets_manager.py` (icons/emojis/sounds, frozen-vs-source path handling),
`src/utils.py` (single-instance Windows mutex + `SingletonMeta`), `src/logger_config.py`
(loguru, rotating logs under `logs/`).

Config is a JSON file (`biryani_config.json`) next to the exe when frozen, or at the package
root when run from source. `settings.ini` is legacy and unused.

## Conventions & gotchas

- **Windows-only**: relies on `powercfg`, `win32com`, and `kernel32` mutex. `pywin32` is an
  optional `windows` extra in pyproject but is imported unconditionally.
- **Edit the GUI with care**: `src/settings_gui.py` (~2300 lines) is largely AI-generated;
  the author's top-of-file comment says to rewrite rather than patch. It has heavy
  duplication and some latent bugs (see below). Prefer surgical changes.
- **Frozen vs source paths**: anything touching assets/config must handle `sys.frozen`
  (see `assets_manager.py` and `app_config_manager.py`) — test both modes.
- **Naming**: package/exe metadata is misspelled "birayni" in `pyproject.toml` and
  `build.py`; user-facing strings use "biryani". Keep new code on "biryani".
- **Two build tools** appear (cx_Freeze is the real one used by the installer; pyinstaller is
  only a leftover dev dependency). Use cx_Freeze.
- **`requirements.txt` is stale** — `pyproject.toml` + `uv.lock` are the source of truth. Dependency management uses `uv`.
- After changing notification logic, verify in BOTH the running app and that the bg process
  actually picks up `settings_updated_flag`.

## Out of scope

`website/` is an untouched create-t3-app scaffold (placeholder, not wired to anything).
