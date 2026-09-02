# Seawhirl

`seawhirl` is a Python package for accelerating CLI spinners.

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

Use `python -m seawhirl --help` to see all available configuration flags.

## Structure

<details>
<summary>(Click to expand)</summary>

```text
seawhirl/
  ├── _cli/
  │   └── cli.py: Command-line argument parsing
  ├── _core/
  │   ├── data/
  │   │   └── presets.json: Default spinner animation frames
  │   ├── backends.py: Threading and asyncio backends for rendering
  │   ├── easing.py: Mathematical easing curves and physics
  │   ├── engine.py: The core rendering engine for the spinner
  │   ├── exceptions.py: Custom exceptions for the seawhirl package
  │   ├── presets.py: Preset configurations loaded from JSON
  │   ├── terminal.py: Terminal interaction and cursor manipulation utilities
  │   └── utils.py: Utility functions for the package
  ├── _lib/
  │   └── spinner.py: The main `Spinner` class, context manager and decorator
  ├── __init__.py: Exposes the public API
  ├── __main__.py: The entry point for the package
  └── py.typed: Marker file for PEP 561 typing support
```
</details>

## Installation

Follow these steps to install `seawhirl`:

1. **Prerequisites**: Verify that you have Python 3.10 or later. You can install Python at `https://www.python.org/downloads/`. Install Git at `https://git-scm.com/install/`.

2. **Install the package**: Install `seawhirl` and its dependencies using pip.

    ```bash
    pip install git+[https://github.com/adamggrim/seawhirl.git](https://github.com/adamggrim/seawhirl.git)
    ```
    *Note: On macOS/Linux, you may need to use `pip3` instead of `pip`*.

## Usage

Add a spinner to scripts with either a context manager or a decorator.

### 1. Context manager

Wrap specific blocks of code using the `with` statement.

```python
import time
from seawhirl import Spinner

with Spinner(accel_secs=6.0, status_text='Whirl up sea'):
    time.sleep(6)
```

### 2. Decorator

Apply the spinner to a function.

```python
import time
from seawhirl import Spinner, Spring

spinner = Spinner(
    easing=Spring(tension=6.0, friction=8.0),
    oscillation=True
)

@spinner
def process_data(filepath: str):
    time.sleep(5)
    return f'Processed {filepath}'

result = process_data('data.csv')
```

## License

This project is licensed under the MIT License.

## Contributors

- Adam Grim (@adamggrim)
