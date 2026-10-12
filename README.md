# Seawhirl

[![CI](https://github.com/adamggrim/seawhirl/actions/workflows/ci.yml/badge.svg)](https://github.com/adamggrim/seawhirl/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`seawhirl` is a Python package for accelerating terminal spinners.

## Requirements

- Python 3.10+

## Previews

Preview spinners directly in the terminal.

Run the default spinner:
```bash
python -m seawhirl
```

Try built-in presets (`whirl`, `arc`, `blink`, `bounce`, `dots`, `line`):
```bash
python -m seawhirl dots --duration 10
```

Animate custom frames:
```bash
python -m seawhirl --custom "🌑,🌒,🌓,🌔,🌕,🌖,🌗,🌘" --accel 1.5
```

Add colors:
```bash
python -m seawhirl --easing sine --oscillation --color "cyan,magenta"
```

Use `python -m seawhirl --help` to see all available configuration flags.

## Structure

<details>
<summary>(Click to expand)</summary>

```text
seawhirl/
  ├── _cli/
  │  └── cli.py: Command-line argument parsing
  ├── _core/
  │  ├── backends.py: Threading and asyncio backends for rendering
  |  ├── colors.py: Color parsing utilities
  │  ├── config.py: Spinner configuration objects
  │  ├── easing.py: Mathematical easing curves and physics
  │  ├── engine.py: The core spinner rendering engine
  │  ├── exceptions.py: Custom exceptions for spinners
  |  ├── palette.py: Color palette definitions
  │  ├── presets.py: Preset spinner configurations
  │  ├── terminal.py: Terminal interaction and cursor manipulation
  │  └── utils.py: Universal utility functions
  ├── _lib/
  │  └── spinner.py: The main `Spinner` class, context manager and decorator
  ├── __init__.py: Exposes the public API
  ├── __main__.py: The entry point for the package
  └── py.typed: Marker file for PEP 561 typing support
```
</details>

## Installation

Follow these steps to install `seawhirl`:

1. **Prerequisites**: Verify that you have Python 3.10 or later. You can install Python at [python.org/downloads](https://www.python.org/downloads/) and Git at [git-scm.com/install](https://git-scm.com/install/).

2. **Install the package**: Install `seawhirl` and its dependencies using pip.

    ```bash
    pip install git+https://github.com/adamggrim/seawhirl.git
    ```

## Usage

Add a spinner to scripts with either a context manager or decorator. Apply a custom array of colors that accelerates with the spinner.

### 1. Context manager

Wrap specific blocks of code using the `with` statement.

```python
import time
from seawhirl import Spinner

with Spinner(
    accel_secs=6.0,
    status_text='Whirl up sea...'
):
    time.sleep(6)
```

### 2. Decorator

Apply the spinner to a function.

```python
import time
from seawhirl import Spinner, Spring

spinner = Spinner(
    easing=Spring(tension=6.0, friction=8.0),
    oscillation=True,
    color=('#0055ff', '#00ffaa')
)

@spinner
def process_data(filepath: str):
    time.sleep(5)
    return f'Processed {filepath}'

result = process_data('data.csv')
```

### 3. Colors

Monotonic curves (`Logarithmic`, `Inertial`) map an accelerating color sequence across the curve.

Wave-based curves (`Sinusoidal`, `Spring`) support two modifier methods:

**Normalized (default)**
Moves through all color stops from trough to crest, then reverses direction from crest to trough.

```python
from seawhirl import Sinusoidal, Spinner

spinner = Spinner(
    easing=Sinusoidal().normalized(),
    oscillation=True,
    color=['#0055ff', '#00ffaa', '#ff0066']
)
```

**Indexed**
Moves from one color stop to the next from trough to crest, then moves to a new color stop at the next trough.

```python
spinner = Spinner(
    easing=Sinusoidal().indexed(),
    oscillation=True,
    color=['#0055ff', '#00ffaa', '#ff0066']
)
```

## License

This project is licensed under the MIT License.

## Contributors

- Adam Grim (@adamggrim)
