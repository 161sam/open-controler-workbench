# Installation

## Module root requirement

This repository is the FreeCAD module root.

FreeCAD expects the following structure directly in the module directory:

```text
OpenControllerWorkbench/
├── Init.py
├── InitGui.py
├── ocw_workbench/
├── ocw_kicad/
└── resources/
```

Always link or copy the repository root itself. Do not point FreeCAD only at `ocw_workbench/`.

## Requirements

- FreeCAD
- Python and `pip`
- Git
- `PyYAML` available in the Python environment used by FreeCAD

## Recommended GitHub release install

For `v0.1.0`, the recommended end-user distribution path is the GitHub Release asset:

- `ocw-workbench-v0.1.0-freecad-mod.zip`

Install steps:

1. Download the zip from the GitHub Release page.
2. Extract it so the top-level folder is `OpenControllerWorkbench/`.
3. Copy or move that folder into the FreeCAD `Mod` directory.
4. Make sure `PyYAML` is available to FreeCAD's Python interpreter.
5. Restart FreeCAD.

## Linux development install

```bash
git clone https://github.com/161sam/open-controller-workbench.git
cd open-controller-workbench
pip install -e .
mkdir -p ~/.local/share/FreeCAD/Mod
ln -s "$(pwd)" ~/.local/share/FreeCAD/Mod/OpenControllerWorkbench
```

## Snap FreeCAD development install

```bash
git clone https://github.com/161sam/open-controller-workbench.git
cd open-controller-workbench
pip install -e .
mkdir -p ~/snap/freecad/common/Mod
ln -s "$(pwd)" ~/snap/freecad/common/Mod/OpenControllerWorkbench
```

## Startup check

1. Start FreeCAD.
2. Open the workbench selector.
3. Select `Open Controller Workbench`.

If installation is correct:

- FreeCAD finds `InitGui.py`
- the workbench appears in the workbench list
- icons load
- templates, variants, and library YAML data are available

## Troubleshooting

### Workbench does not appear

- Confirm the symlink points to the repository root.
- Confirm `Init.py` and `InitGui.py` are directly inside the target directory.
- Restart FreeCAD completely.

### Icons are missing

- Confirm `resources/icons/` exists in the linked module root.
- Confirm only the repository root is linked, not `ocw_workbench/` alone.

### YAML template or library data is missing

- Confirm these paths exist in the linked module root:
  - `ocw_workbench/templates/`
  - `ocw_workbench/variants/`
  - `ocw_workbench/library/`
  - `ocw_workbench/plugins/internal/`
- Confirm FreeCAD loaded the expected module directory.

### Import errors

- Re-run `pip install -e .`
- Verify which Python environment your FreeCAD build uses

## Distribution note

`v0.1.0` is distributed primarily through GitHub Release assets.
The source distribution and wheel are published as secondary technical artifacts, not as the main end-user installation format.
