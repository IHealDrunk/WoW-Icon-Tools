# Changelog

## [1.2.0] - 2026-10-08

### Added
- Added three build options when an existing `ICONS` folder is detected:
  - **Resume Build** — continue processing missing icons without rebuilding completed icons.
  - **Start Over** — clear generated output and rebuild the icon set.
  - **Cancel** — exit without starting the build.
- Added a review workflow for non-standard icon dimensions.
  - Icons that are not 64×64 are copied to the `REVIEW` folder.
  - Original filenames and subfolder structures are preserved.
  - Existing review copies are not overwritten.
- Added the **Onyx** icon template, including the PNG texture, editable GIMP XCF file, and template configuration.

### Improved
- Updated `resize_png.py` to separate standard icons from those requiring manual review.
- Improved resizing output to display counts for processed, previously processed, review-required, and failed icons.
- Improved directory handling and output organization.
- Updated `.gitignore` to exclude generated review files from version control.

### Fixed
- Corrected build cleanup behavior to preserve `.gitkeep` files.
- Removed generated review files from Git tracking.

### Changed
- Removed CASCExplorer from the tracked project files.
- Standard 64×64 icons continue through the existing resizing and cropping process.