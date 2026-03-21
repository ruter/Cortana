## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-03-21 - [Test Suite Import Workarounds]
**Learning:** The test suite manipulates `sys.path` directly (e.g. `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))`), which causes issues with standard relative imports within the `src/` modules during test execution if they're not fully qualified or if the module acts as a top-level script in tests.
**Action:** When updating import statements in `src/` files, avoid refactoring existing relative imports (like `from .config import config`) to explicit relative or absolute unless they break the production app, as the test suite expects the files to be able to import their siblings without standard package structures. If tests break on relative imports, you must add `try...except ImportError` blocks with absolute imports as fallbacks instead.
