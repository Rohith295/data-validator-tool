# Examples

These notebooks are meant to be run from a local clone of the repository.

They use the existing `sample_data/` files and the public Python API:

- `api_quickstart.ipynb` shows in-memory validation with `validate()` and `ReportView`
- `sample_files_walkthrough.ipynb` shows file-based validation with `validate_file()`

Recommended setup:

```bash
pip install -e ".[dev]"
```

If Jupyter is not installed yet:

```bash
pip install notebook
```

Then start Jupyter from the project root:

```bash
jupyter notebook
```

The notebooks include a small path check so they still work if the current working directory is the `examples/` folder.
