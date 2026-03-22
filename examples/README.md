# Examples

These notebooks are meant to be run from a local clone of the repository.

They use the existing `sample_data/` files and the public Python API:

- `api_quickstart.ipynb` shows in-memory validation with `validate()` and `ReportView`
- `sample_files_walkthrough.ipynb` shows file-based validation with `validate_file()`

Recommended setup:

```bash
pip install -e ".[dev]"
```

Register the virtualenv as a notebook kernel:

```bash
python -m ipykernel install --user --name data-validator --display-name "Python (data-validator)"
```

Then start Jupyter from the project root:

```bash
jupyter notebook
```

When you open a notebook, select the `Python (data-validator)` kernel.

The notebooks include a small path check so they still work if the current working directory is the `examples/` folder.
