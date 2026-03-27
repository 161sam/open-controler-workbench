# Release Process

## Scope

This document describes the GitHub release workflow prepared for `v0.1.0`.

## Distribution model

Primary publication target:

- GitHub Release assets

Why this is the primary path:

- OCW is a FreeCAD workbench that expects a module-root directory layout
- end users benefit most from a downloadable archive they can unpack directly into the FreeCAD `Mod` directory
- GitHub Releases provide a simple place for release notes, checksums, and installable assets together

Secondary technical artifacts:

- Python `sdist`
- Python `wheel`

These are useful for reproducibility and development tooling, but they are not the main end-user installation format for FreeCAD.

GitHub Packages is not used as the primary distribution path for `v0.1.0` because:

- it does not map cleanly to the FreeCAD module-root installation model
- it adds registry friction for users who mainly need a downloadable workbench bundle
- Release assets are easier to document and support for an alpha workbench release

## Release trigger

The repository contains one release workflow:

- `.github/workflows/release-v0.1.yml`

It supports two trigger paths:

1. Push the exact tag `v0.1.0`
2. Run the workflow manually with `workflow_dispatch`

## Release notes source

The workflow uses:

- `RELEASE_NOTES_v0.1.md`

This is intentional. For the first release, a fixed file is more robust than auto-generated notes.

## Produced release artifacts

The workflow publishes these artifacts to the GitHub Release:

- source distribution: `dist/ocw-workbench-0.1.0.tar.gz`
- wheel distribution: `dist/ocw_workbench-0.1.0-py3-none-any.whl`
- workbench module archive:
  - `dist/release/ocw-workbench-v0.1.0-freecad-mod.zip`
- checksum file:
  - `dist/release/ocw-workbench-v0.1.0-sha256.txt`

The workbench archive is meant for users who want the FreeCAD module-root layout directly.
The checksum file covers the zip, sdist, and wheel artifacts uploaded for the release.

## Workflow behavior

The workflow performs these steps:

1. Check out the repository with tags
2. Set up Python 3.12
3. Validate the release tag metadata
4. Install build tooling
5. Run release sanity tests
6. Build `sdist` and `wheel`
7. Build the module-root workbench zip archive
8. Generate a SHA256 checksum file for all release assets
9. Create the GitHub Release and upload all release assets

## Draft vs published

- Tag-triggered runs publish a non-draft release by default
- Manual runs allow setting `draft: true`

This supports a release-manager flow where the asset build can be checked before final publication.

## Required GitHub permissions

The workflow uses:

- `contents: write`

No custom secrets are required beyond the standard `GITHUB_TOKEN`.

## How to create the v0.1.0 release

### Recommended path

1. Confirm `CHANGELOG.md`, `RELEASE_NOTES_v0.1.md`, and `README.md` are up to date.
2. Run the release sanity tests locally.
3. Push the release commit.
4. Create and push tag `v0.1.0`.
5. Wait for `.github/workflows/release-v0.1.yml` to complete.
6. Inspect uploaded assets, checksum file, and the generated GitHub Release page.

### Manual dry-run style path

1. Open the GitHub Actions tab.
2. Run `Release v0.1` manually.
3. Keep `tag_name = v0.1.0`.
4. Set `draft = true`.
5. Inspect the draft release and uploaded artifacts.

## End-user installation path from GitHub

Recommended end-user artifact:

- `ocw-workbench-v0.1.0-freecad-mod.zip`

Install steps:

1. Download the zip from the GitHub Release page.
2. Extract it so the resulting top-level folder is `OpenControllerWorkbench/`.
3. Copy or move that folder into the FreeCAD `Mod` directory.
4. Ensure `PyYAML` is available in the Python environment used by FreeCAD.
5. Restart FreeCAD and select `Open Controller Workbench`.

## Notes for later releases

This workflow is intentionally narrow for the first release.

For later versions, update or generalize:

- tag pattern
- release notes file selection
- asset naming
- release checklist references
