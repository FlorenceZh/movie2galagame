# Repository Guidelines

## Project Structure & Module Organization
This repository is a small Python utility that extracts frames, audio clips, and a script file from a video and subtitle pair.

- `main.py` contains the core `Engine` class and entry point.
- `requirements.txt` lists runtime dependencies (`moviepy`, `pysrt`).
- `output/` is the default generated output folder.
- Video and subtitle files (`.mp4`, `.srt`) currently live in the repo root as examples.

## Build, Test, and Development Commands
Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the tool (uses the hard-coded paths in `main.py`):

```bash
python main.py
```

Outputs are written to `output/images/`, `output/audio/`, and `output/script.rpy`.

## Coding Style & Naming Conventions
- Language: Python 3.
- Indentation: 4 spaces.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes.
- Keep file paths as `pathlib.Path` where possible (already used in `main.py`).

## Testing Guidelines
There is an automated test suite.

- Place tests under `tests/` and name them `test_*.py`.
- Run them using: `python3 -m unittest discover tests`

## Commit & Pull Request Guidelines
Recent commit messages are short and direct (e.g., "Update README.md", "Create ffmpeg.exe").
Use imperative, concise subjects and include relevant context in the body when needed.

Pull requests should include:

- A clear summary of changes.
- Links to related issues (if any).
- Screenshots or sample outputs when changing generated media or script output.

## Configuration & Runtime Notes
- The current entry point uses hard-coded input paths in `main.py`.
- If you make this configurable, document the new flags or config file here.
