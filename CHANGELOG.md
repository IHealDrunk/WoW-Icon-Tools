# Changelog

## [1.3.0] - 2026-10-14

- Updated the remaining-time label on all status bars.
- Separate cached bad BLPs and review files from new failures in the build summary.
- Consolidated legacy image validation and duration formatting; removed an unused template loader.

- Added Pause/Resume and persistent Save & Exit with atomic recovery checkpoints.
- Added SHA-256 detection of new/modified BLPs, intermediates, and exports.
- Cache failed BLP hashes; retry only changed sources.
- Added separate completion histories for all templates and adoption of existing icon sets.
- Apply edited templates incrementally; full rebuilds remain an explicit Start Over choice.
- Added native 128×128 inputs alongside the original 64×64 upscale/crop workflow.
- Added GIMP batches of up to 32 icons with one loaded template, fresh image duplicates,
  individual completion tracking, and isolated retry of unfinished/failed batch members.
- Added estimated time remaining and a shared progress layout for all three stages.
- Amortized checkpoint writes and preserved compatibility with older recovery files.
- Added BLP2 raw BGRA support and case-insensitive nested input/output paths.
- Regenerate stale intermediates and prevent failed conversions from using old PNGs.
- Consolidated decoding into blp_to_png.py and checkpoint/control helpers into utils.py.
- Preserved v1.2.0 build choices, confirmed cleanup, template metadata, and review routing.
- Added fixtures for format support, skipping, template rotation, adoption, recovery,
  128×128 preservation, ETA, and atomic exports.

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