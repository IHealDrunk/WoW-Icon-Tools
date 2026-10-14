from time import perf_counter
import shutil
import json
import signal
from utils import (BuildState, BuildControl, SaveAndExit, sha256, path_key,
                   RESIZED_FOLDER, ICONS_FOLDER)

from blp_to_png import convert_blp_to_png
from resize_png import resize_icons
from load_template import (
    select_template,
    load_template,
)
from gimp_render import render_batch, validate_template, BATCH_SIZE
from PIL import Image
from console import (
    app_header,
    section,
    info,
    success,
    warning,
    error,
    StageProgress,
    labeled_value,
    build_summary,
    duration_text,
)


def clear_icons_folder() -> bool:
    """
    Delete all generated contents of the ICONS folder.

    The ICONS folder itself and .gitkeep are preserved.

    Returns True if the folder was cleared
    successfully.
    """

    try:

        for item in ICONS_FOLDER.iterdir():

            # Never delete .gitkeep
            if item.name == ".gitkeep":
                continue

            if item.is_dir():
                shutil.rmtree(item)

            else:
                item.unlink()

        return True

    except OSError as clear_error:

        print()
        error(
            "Could not completely clear "
            "the ICONS folder."
        )

        print()
        print(clear_error)

        return False


def confirm_existing_icons() -> bool:
    """
    Check whether the ICONS folder already
    contains files.

    The user may:

    1. Resume the existing build.
    2. Delete existing output and start over.
    3. Cancel the build.
    """

    # No output folder yet.
    if not ICONS_FOLDER.exists():
        return True

    # Output folder exists but is empty.
    if not any(p.name != ".gitkeep" for p in ICONS_FOLDER.iterdir()):
        return True

    print()

    warning(
        "Existing icons detected in "
        "the ICONS folder."
    )

    print()
    print(
        "WoW Icon Tools can resume the previous "
        "build or start over."
    )

    print()
    print("[1] Resume Build")
    print("    Skip completed icons and continue.")

    print()
    print("[2] Start Over")
    print(
        "    Delete existing icons and "
        "rebuild everything."
    )

    print()
    print("[3] Cancel")

    print()

    while True:

        choice = input(
            "Select an option: "
        ).strip()

        # -------------------------
        # Resume Build
        # -------------------------

        if choice == "1":

            print()
            info(
                "Resuming build. Existing "
                "finished icons will be checked and reused when unchanged."
            )

            return True

        # -------------------------
        # Start Over
        # -------------------------

        if choice == "2":

            print()

            warning(
                "START OVER will permanently delete "
                "all files in the ICONS folder."
            )

            print()
            print(
                "This action cannot be undone."
            )

            print()

            confirmation = input(
                "Type YES to confirm: "
            ).strip()

            if confirmation != "YES":

                print()
                warning(
                    "Start Over cancelled. "
                    "No files were deleted."
                )

                continue

            print()
            info(
                "Clearing existing icons..."
            )

            if not clear_icons_folder():

                print()
                error(
                    "Build cancelled because the "
                    "ICONS folder could not be cleared."
                )

                return False

            print()
            success(
                "ICONS folder cleared."
            )

            print()
            info(
                "Starting a fresh build."
            )

            return True

        # -------------------------
        # Cancel
        # -------------------------

        if choice == "3":

            return False

        print()

        warning(
            "Please select 1, 2, or 3."
        )

        print()


def run_build(state, control):

    build_start_time = perf_counter()

    app_header()
    info("Preparing icon pipeline...")

    # Check for existing finished icons
    if not confirm_existing_icons():

        print()
        warning("Build cancelled.")

        return

    # Step 1 - Convert BLP files
    section("Checking and Converting BLP Files")

    state.data.update(stage_errors=0, known_bad_blps=0, review_count=0)
    png_inputs = convert_blp_to_png(state, control)

    # Step 2 - Resize PNG files
    section("Resizing PNG Files")

    png_files = resize_icons(state, control, png_inputs)

    # Step 3 - Choose a template
    template_name = state.data.get("template")
    if template_name:
        choice = input(f'Recover template "{template_name}"? [Y] Recover / [N] Select another: ').strip().casefold()
        if choice != 'y':
            template_name = None
    template_name = template_name or select_template()

    if template_name is None:

        print()
        warning("Build cancelled.")

        return

    # Step 4 - Load the selected template
    template, _template_folder = load_template(
        template_name
    )

    if template is None:

        print()

        error(
            f'Template "{template_name}" '
            "could not be loaded."
        )

        return

    valid, reason = validate_template(template)
    if not valid:
        error(reason)
        return
    if template['icon_size'] != 128:
        error('This pipeline requires a 128x128 template.')
        return
    template['folder_name'] = template_name
    state.data['template'] = template_name
    state.data['status'] = 'running'
    state.save()
    template_fingerprint = sha256(template['template_path']) + json.dumps(
        {k: template[k] for k in ('replace_layer', 'icon_size', 'export_format')}, sort_keys=True)

    section("Selected Template")

    labeled_value(
        "Name",
        template["name"]
    )

    labeled_value(
        "Author",
        template.get(
            "author",
            "Unknown"
        )
    )

    labeled_value(
        "Version",
        template.get(
            "version",
            "Unknown"
        )
    )

    labeled_value(
        "Icon Size",
        f'{template["icon_size"]}×'
        f'{template["icon_size"]}'
    )

    labeled_value(
        "Export Format",
        template["export_format"]
    )

    # Step 5 - Find resized PNG files
    png_files = sorted(png_files)

    total = len(png_files)

    print()

    info(
        f"Found {total} resized PNG file(s)."
    )

    if total == 0:

        print()

        error(
            "No resized PNG files were found."
        )

        print()
        print("Expected folder:")
        print(RESIZED_FOLDER)

        return

    # Step 6 - Prepare output folder
    ICONS_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    section("Rendering Icons")

    state.migrate_render_history(template_name, template_fingerprint)
    records = state.template_history(template_name)['records']
    extension = '.' + template['export_format'].lower().lstrip('.')
    unrecorded = sum(1 for source in png_files
                     if path_key(source.relative_to(RESIZED_FOLDER)) not in records
                     and (ICONS_FOLDER / source.relative_to(RESIZED_FOLDER).with_suffix(extension)).is_file())
    adopt_existing = False
    if unrecorded:
        print(f'\nFound {unrecorded} existing icons without history for {template_name}.')
        print(f'[1] Use these as the existing {template_name} set')
        print('    Confirms they already match this template and the current source icons.')
        print('[2] Rebuild icons without history')
        print('[3] Cancel')
        while True:
            choice = input('Select an option: ').strip()
            if choice in ('1', '2', '3'):
                break
        if choice == '3':
            return
        adopt_existing = choice == '1'
    rendered, skipped, failed = render_icons(
        template, png_files, state, control, template_fingerprint, adopt_existing)

    control.boundary()
    state.data['status'] = 'complete' if failed == 0 and not state.data.get('stage_errors') else 'incomplete'
    state.save()

    elapsed_time = (
        perf_counter()
        - build_start_time
    )

    build_summary(
        template_name=template["name"],
        total=total,
        rendered=rendered,
        skipped=skipped,
        failed=failed + state.data.get('stage_errors', 0),
        elapsed_time=duration_text(elapsed_time, include_seconds=True),
        output_folder=ICONS_FOLDER,
        known_bad=state.data.get('known_bad_blps', 0),
        review=state.data.get('review_count', 0),
    )


def render_icons(template, png_files, state, control, template_fingerprint, adopt_existing=False):
    rendered = skipped = failed = adopted = checked = 0
    template_name = template.get('folder_name', template.get('name', 'default'))
    extension = '.' + template['export_format'].lower().lstrip('.')
    display = StageProgress(len(png_files), control)
    pending = []
    fingerprints = {}
    records = state.template_history(template_name)['records']
    print(f'Checking {len(png_files)} icon(s) for {template_name}; completed exports are reused.')
    for png_file in png_files:
        control.boundary()
        relative = png_file.relative_to(RESIZED_FOLDER)
        output_file = ICONS_FOLDER / relative.with_suffix(extension)
        try:
            source_hash = sha256(png_file)
            if state.render_current(template_name, relative, source_hash, output_file):
                skipped += 1
                checked += 1
            elif adopt_existing and path_key(relative) not in records and output_file.is_file():
                # Adoption is an explicit user assertion of template/source identity.
                # Reject incomplete or incorrectly sized files rather than blessing them.
                try:
                    with Image.open(output_file) as image:
                        valid = image.size == (128, 128)
                        image.load()
                except (OSError, ValueError):
                    valid = False
                if valid:
                    state.render_complete(template_name, relative, source_hash, output_file, template_fingerprint)
                    skipped += 1
                    adopted += 1
                    checked += 1
                else:
                    pending.append((png_file, output_file))
                    fingerprints[png_file] = source_hash
            else:
                pending.append((png_file, output_file))
                fingerprints[png_file] = source_hash
        except Exception as exc:
            failed += 1
            checked += 1
            print(f'\n[FAILED] {relative}: {exc}')
        display.update(checked, Rendered=rendered, Reused=skipped, Adopted=adopted, Failed=failed)
    state.save()
    display.set_work_remaining(len(pending))
    work_done = 0
    finished = set()
    def completed(source, output, reason):
        nonlocal rendered, failed, checked, work_done
        if source in finished:
            return
        finished.add(source)
        relative = source.relative_to(RESIZED_FOLDER)
        if reason is None:
            try:
                if sha256(source) != fingerprints[source]:
                    reason = 'Source changed during rendering; retry next run'
            except OSError as exc:
                reason = f'Could not verify rendered source: {exc}'
        if reason is None:
            state.render_complete(template_name, relative, fingerprints[source], output, template_fingerprint)
            rendered += 1
        else:
            failed += 1
            print(f'\n[FAILED] {relative}: {reason}')
        checked += 1
        work_done += 1
        display.update(checked, work_done=work_done, Rendered=rendered,
                       Reused=skipped, Adopted=adopted, Failed=failed)
    for offset in range(0, len(pending), BATCH_SIZE):
        control.boundary()
        jobs = pending[offset:offset + BATCH_SIZE]
        try:
            render_batch(template, jobs, completed, control)
        except SaveAndExit:
            raise
        except Exception as exc:
            for source, output in jobs:
                if source not in finished:
                    completed(source, output, str(exc))
        state.save()
    state.save()
    return rendered, skipped, failed


def build_icons():
    state = BuildState(checkpoint_interval=2.0)
    control = BuildControl(state)
    info('Controls: P = Pause, S = Save & Exit; Ctrl+C opens Pause. Active GIMP batches finish safely.')
    previous_handler = signal.signal(signal.SIGINT, control.request_pause)
    try:
        run_build(state, control)
    except SaveAndExit:
        info('Progress saved. Run build_icon.py again to recover.')
    finally:
        signal.signal(signal.SIGINT, previous_handler)


if __name__ == "__main__":
    build_icons()
