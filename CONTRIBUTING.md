# Contributing to bbl-shutter-cam

Thank you for your interest in contributing to this project! This guide covers setting up your development environment and making contributions.

**Before contributing, please review our [Code of Conduct](CODE_OF_CONDUCT.md).**

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Developer Setup](#developer-setup)
- [VSCode Workspace](#vscode-workspace)
- [Running Tasks](#running-tasks)
- [Code Style](#code-style)
- [Testing](#testing)
- [Versioning](#versioning)
- [Submitting Changes](#submitting-changes)

---

## Code of Conduct

This project is committed to providing a welcoming and inspiring community for all participants. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) when interacting with others in the community.

---

## Developer Setup

### Prerequisites

- Python 3.9+
- Git
- A terminal/command prompt

### 1. Clone the Repository

```bash
git clone https://github.com/bodybybuddha/bbl-shutter-cam.git
cd bbl-shutter-cam
```

### 2. Create a Virtual Environment

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -U pip
pip install -e ".[dev]"
```

This installs:
- The package in editable mode (changes take effect immediately)
- All dev tools: pytest, black, pylint, mypy, pyinstaller

### 4. Verify Setup

```bash
bbl-shutter-cam --help
```

---

## VSCode Workspace

This project includes a pre-configured VSCode workspace. If you're using VSCode, you'll get:

- **Recommended extensions** - Auto-prompt to install Python, Pylance, Ruff, GitLens, etc.
- **Pre-configured tasks** - Build, test, lint, and format from the editor
- **Workspace settings** - Python formatter/linter paths, editor rules, exclusions

### Recommended VSCode Extensions

The project will suggest these extensions when opened:

- **Python** (`ms-python.python`) - Core Python support
- **Pylance** (`ms-python.vscode-pylance`) - Type checking and intellisense
- **Ruff** (`charliermarsh.ruff`) - Fast Python linter
- **GitLens** (`eamodio.gitlens`) - Git integration
- **Docker** (`ms-azuretools.vscode-docker`) - For container debugging (optional)

---

## Running Tasks

VSCode tasks are available via keyboard shortcuts or the Command Palette (`Ctrl+Shift+P`):

### Build Tasks

**Ctrl+Shift+B** (or search "Run Build Task"):

| Task | Purpose |
|------|---------|
| **Build executable** ⭐ (default) | Create standalone binary for your platform |
| Build executable (debug) | Build with debug symbols for troubleshooting |

### Test Tasks

**Ctrl+Shift+T** (or search "Run Test Task"):

| Task | Purpose |
|------|---------|
| **Run tests** ⭐ (default) | Execute pytest suite with verbose output |
| Run tests with coverage | Generate HTML coverage report in `htmlcov/` |

### Code Quality Tasks

Search "Run Task" (`Ctrl+Shift+P` → "Tasks: Run Task"):

| Task | Purpose |
|------|---------|
| Install dependencies | Set up dev environment |
| Lint with pylint | Check code style violations |
| Format code with black | Auto-format code to PEP 8 |
| Type check with mypy | Check type annotations |
| Clean build artifacts | Remove `build/`, `dist/`, cache files |
| Dev environment setup | Runs install → format → lint (in sequence) |

### Running Tasks from Terminal

If you prefer the command line:

```bash
# Build
python -m PyInstaller bbl-shutter-cam.spec
# or use the build script:
./scripts/build.sh      # macOS/Linux
scripts\build.bat       # Windows

# Test
python -m pytest tests/ -v
python -m pytest tests/ -v --cov=src/bbl_shutter_cam --cov-report=html

# Lint
python -m pylint src/bbl_shutter_cam/

# Format
python -m black src/ tests/ scripts/

# Type check
python -m mypy src/bbl_shutter_cam/
```

---

## Code Style

This project follows **PEP 8** style guidelines enforced by tool configurations in `pyproject.toml`:

- **Black** - Code formatter (100 character line length, Python 3.9-3.13)
- **Pylint** - Style and error checking (customized for CLI applications)
- **mypy** - Static type checking (Python 3.9 baseline)
- **.editorconfig** - Cross-IDE formatting consistency (UTF-8, LF endings, proper indentation)

### Tool Configuration

All tools are configured in `pyproject.toml` under `[tool.black]`, `[tool.pylint]`, and `[tool.mypy]` sections. The `.editorconfig` file provides additional editor-agnostic settings for all file types.

### Before Committing

Run the "Dev environment setup" task (or manually):

```bash
# Format code
python -m black src/ tests/ scripts/

# Check for issues
python -m pylint src/bbl_shutter_cam/
python -m mypy src/bbl_shutter_cam/
```

### Editor Settings

When using VSCode:
- Format on save is enabled (`Ctrl+S` auto-formats)
- Import sorting is automatic
- Rulers at 100 characters for reference
- 4-space indentation for Python files
- Settings defined in `.vscode/settings.json` and `.editorconfig`

---

## Testing

Tests are located in the `tests/` directory and use **pytest**.

---

## Versioning

This project uses **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`.

- **PATCH** (the last number) for bug fixes and small internal changes that do not change user-facing behavior.
- **MINOR** (the middle number) for new features and backwards-compatible behavior changes.
- **MAJOR** (the first number) for changes that may be breaking (config changes, CLI changes, behavior changes that can affect existing setups).

Examples:

- `1.0.1`: bug fix release
- `1.1.0`: new feature(s) added without breaking existing usage
- `2.0.0`: breaking change release

### Breaking Changes & Deprecations

When a change may break existing setups (CLI flags, config structure/keys/defaults, runtime behavior changes):

- Prefer a deprecation path when practical (warn first, document migration).
- Clearly document the change and the migration steps in `CHANGELOG.md` and relevant `docs/` pages.
- Use SemVer consistently (breaking changes should generally require a MAJOR bump).

---

## Release Process

This section describes how to create and publish a new release.

### Prerequisites

Before creating a release:

1. **All changes merged to `dev`**: Ensure your release branch PR is merged
2. **Quality gates pass**: All tests, lint, type checks passing
3. **Documentation updated**: CHANGELOG.md, ROADMAP.md, README.md, docs/
4. **Local testing complete**: Binary built and tested (see [Building Executables](docs/advanced/building-executables.md#testing-locally-before-release))

### Step 1: Create Release Branch

```bash
# From dev branch
git checkout dev
git pull origin dev

# Create release branch
git checkout -b v1.0.3

# Update dependencies (if needed)
pip install -e ".[dev]" --upgrade

# Build and test locally
./scripts/build.sh
python -m pytest tests/ -v
./dist/bbl-shutter-cam --help
```

### Step 2: Update Version-Related Files

Update version strings and documentation:

1. **CHANGELOG.md**: Add release notes for this version
2. **ROADMAP.md**: Mark completed features, update milestones
3. **README.md**: Update version numbers if referenced
4. **pyproject.toml**: Update version number (if using dynamic versioning)
5. **docs/**: Update any version-specific documentation

### Step 3: Commit and Push

```bash
# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "chore: prepare v1.0.3 release

- Update dependencies
- Update documentation
- Update CHANGELOG.md"

# Push to remote
git push -u origin v1.0.3
```

### Step 4: Create Pull Request

```bash
# Create PR from v1.0.3 -> dev
# Via GitHub UI or CLI:
gh pr create --base dev --head v1.0.3 \
  --title "Release v1.0.3: Brief description" \
  --body "Release notes summary"

# Wait for CI checks to pass
# Review and merge the PR
```

### Step 5: Tag the Release

After the PR is merged to `dev`:

```bash
# Switch to dev and pull the merged changes
git checkout dev
git pull origin dev

# Create annotated tag
git tag -a v1.0.3 -m "Release v1.0.3

Brief description of this release.

Key improvements:
- Feature 1
- Feature 2
- Bug fix 3"

# Push the tag
git push origin refs/tags/v1.0.3
```

### Step 6: Create GitHub Release

The tag alone won't trigger the build workflow. You must publish a GitHub Release:

1. **Go to GitHub Releases**: https://github.com/bodybybuddha/bbl-shutter-cam/releases
2. **Click "Draft a new release"**
3. **Choose the tag**: Select `v1.0.3` from the dropdown
4. **Add release title**: `v1.0.3 - Brief Description`
5. **Add release notes**: Copy/paste from CHANGELOG.md and format nicely
6. **Mark as pre-release** (optional): Check if this is a pre-release
7. **Click "Publish release"**

**This triggers the GitHub Actions workflow** which will:
- Build binaries for Linux ARM64 and ARMv7
- Upload binaries as release assets automatically
- Complete in ~5-10 minutes

### Step 7: Verify Release

After the workflow completes:

1. **Download a binary**: Test one of the uploaded artifacts
2. **Verify it works**: Run `--help`, test basic functionality
3. **Check release notes**: Ensure they're formatted correctly
4. **Update documentation** (if needed): Fix any issues found

### Step 8: Merge to Main (Optional)

For stable releases, merge `dev` → `main`:

```bash
# Create PR: dev -> main
gh pr create --base main --head dev \
  --title "Release v1.0.3" \
  --body "Merge stable release to main"

# Review and merge
```

### Troubleshooting Releases

**Workflow didn't trigger?**
- The workflow triggers on `release: types: [published]`, not on tag push
- You must create and publish the GitHub Release (Step 6)
- You can manually trigger via Actions tab → Release → Run workflow

**Need to rebuild a release?**
- Go to Actions → Release workflow → Run workflow
- Enter the tag name (e.g., `v1.0.3`)
- Binaries will be uploaded to the existing release

**Tag already exists?**
```bash
# Delete the tag locally and remotely
git tag -d v1.0.3
git push origin :refs/tags/v1.0.3

# Recreate and push
git tag -a v1.0.3 -m "..."
git push origin refs/tags/v1.0.3
```

---

## Maintainer Notes (Repo Policy)

These are typically enforced via GitHub branch protection rules:

- Protect `main` and `dev` (require PRs; no direct pushes).
- Require status checks (at minimum: lint/test, PR Policy; optionally PR Title).
- Require reviews for sensitive areas (see `.github/CODEOWNERS`).

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Specific Test

```bash
python -m pytest tests/test_config.py -v
pytest tests/test_config.py::test_load_profile -v
```

### Coverage Report

Generate HTML coverage report:

```bash
python -m pytest tests/ -v --cov=src/bbl_shutter_cam --cov-report=html
```

View report: Open `htmlcov/index.html` in your browser.

### CI Expectations

GitHub Actions runs lint and tests on every PR to `main` and `dev`:
- **Lint**: black, pylint, mypy
- **Tests**: pytest with an 80% coverage gate

Make sure your changes pass locally before opening a PR:

```bash
python -m pytest tests/ -v
python -m black --check src/ tests/ scripts/
python -m pylint src/bbl_shutter_cam/
python -m mypy src/bbl_shutter_cam/
```

### Writing Tests

- Test files go in `tests/` with `test_*.py` naming
- Use descriptive test names: `test_load_profile_missing_file_raises_error()`
- Test structure: Arrange → Act → Assert

Example:

```python
def test_load_profile_missing_file_raises_error():
    """Test that loading a missing profile raises FileNotFoundError."""
    # Arrange
    missing_path = Path("/tmp/nonexistent.toml")

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        load_config(missing_path)
```

---

## Project Structure

```
bbl-shutter-cam/
├── src/bbl_shutter_cam/        # Main package
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   ├── discover.py             # BLE discovery & orchestration
│   ├── ble.py                  # Bluetooth utilities
│   ├── config.py               # Config file handling
│   ├── camera.py               # Camera capture wrapper
│   ├── util.py                 # Utilities
│   ├── logging_config.py       # Logging setup
│   └── py.typed                # Type hint marker
├── tests/                      # Test suite (pytest)
├── docs/                       # User documentation (Jekyll + GitHub Pages)
├── scripts/                    # Build scripts
├── examples/                   # Example configuration
├── .vscode/                    # VSCode configuration
│   ├── extensions.json         # Recommended extensions
│   ├── tasks.json              # Build/test tasks
│   └── settings.json           # (local, not committed)
├── .github/                    # GitHub workflows (CI/CD)
├── .editorconfig               # Cross-IDE formatting rules
├── pyproject.toml              # Project metadata, dependencies, tool configs
├── bbl-shutter-cam.spec        # PyInstaller configuration
├── CHANGELOG.md                # Release history
├── CODE_OF_CONDUCT.md          # Community guidelines
├── CONTRIBUTING.md             # This file
├── README.md                   # User guide
├── LICENSE                     # MIT License
└── .gitignore
```

---

## Submitting Changes

### 1. Create a Branch

Post-v1, all work is done in short-lived branches created from `dev`, and merged back into `dev` via pull requests.

```bash
git checkout dev
git pull --ff-only
git checkout -b feature/my-feature
```

Branch naming conventions:

- `feature/<short-description>` for new features
- `bugfix/<short-description>` for bug fixes

PR target rules:

- Open PRs into `dev`
- Only merge `dev` into `main` for releases (release PR should be `dev` → `main`)

### 2. Make Changes

Write code, add tests, update docs. Commit frequently with clear messages:

```bash
git add .
git commit -m "Add feature: description of change"
```

### 3. Test Locally

Run the full test suite and linting:

```bash
python -m pytest tests/ -v
python -m pylint src/bbl_shutter_cam/
python -m mypy src/bbl_shutter_cam/
python -m black src/ tests/ --check  # Verify formatting
```

Or run the "Dev environment setup" task in VSCode.

### 4. Push and Create Pull Request

```bash
git push origin feature/my-feature
```

Then open a Pull Request on GitHub (target `dev`). Include:
- Description of what changed and why
- Relevant issue numbers (e.g., "Closes #42")
- Screenshots if UI-related
- Test results

### 5. Code Review

Maintainers will review your changes. Be responsive to feedback!

---

## Common Development Tasks

### Add a New CLI Command

1. Add subcommand to `_build_parser()` in `cli.py`
2. Implement `_cmd_yourcommand()` handler
3. Add logic to appropriate module (discover.py, config.py, etc.)
4. Add tests in `tests/test_cli.py`
5. Update [docs/advanced/extending.md](docs/advanced/extending.md)

### Add Configuration Options

1. Update example config: `examples/config.example.toml`
2. Update schema handling in `config.py`
3. Update documentation in `docs/user-guide/profiles.md`
4. Add tests for new config keys

### Build Standalone Executable

See [Building Executables Guide](docs/advanced/building-executables.md):

```bash
./scripts/build.sh      # macOS/Linux
scripts\build.bat       # Windows
```

---

## Getting Help

- **Questions?** Check [FAQ](docs/faq.md) or [Troubleshooting](docs/troubleshooting.md)
- **Implementation details?** See [docs/advanced/extending.md](docs/advanced/extending.md)
- **Report bugs?** Open a [GitHub Issue](https://github.com/bodybybuddha/bbl-shutter-cam/issues)

---

## Questions?

Feel free to open a GitHub Discussion or Issue. We're here to help!

Thank you for contributing! 🎉
