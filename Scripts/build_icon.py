from time import perf_counter
import shutil

from blp_to_png import convert_blp_to_png
from resize_png import resize_icons
from utils import RESIZED_FOLDER, ICONS_FOLDER
from load_template import (
    select_template,
    load_template,
)
from gimp_render import render_icon
from console import (
    app_header,
    section,
    info,
    success,
    warning,
    error,
    progress,
    labeled_value,
    build_summary,
)


def format_elapsed_time(seconds: float) -> str:
    """
    Convert elapsed seconds into a readable time.
    """

    total_seconds = int(seconds)

    hours, remainder = divmod(
        total_seconds,
        3600
    )

    minutes, seconds = divmod(
        remainder,
        60
    )

    if hours > 0:
        return (
            f"{hours}h "
            f"{minutes}m "
            f"{seconds}s"
        )

    if minutes > 0:
        return (
            f"{minutes}m "
            f"{seconds}s"
        )

    return f"{seconds}s"


def clear_icons_folder() -> bool:
    """
    Delete all contents of the ICONS folder.

    The ICONS folder itself is preserved.

    Returns True if the folder was cleared
    successfully.
    """

    try:

        for item in ICONS_FOLDER.iterdir():

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
    if not any(ICONS_FOLDER.iterdir()):
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
                "finished icons will be skipped."
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


def build_icons():

    build_start_time = perf_counter()

    app_header()
    info("Preparing icon pipeline...")

    # Check for existing finished icons
    if not confirm_existing_icons():

        print()
        warning("Build cancelled.")

        return

    # Step 1 - Convert BLP files
    section("Converting BLP Files")

    convert_blp_to_png()

    # Step 2 - Resize PNG files
    section("Resizing PNG Files")

    resize_icons()

    # Step 3 - Choose a template
    template_name = select_template()

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
    png_files = sorted(
        RESIZED_FOLDER.glob("*.png")
    )

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

    rendered = 0
    skipped = 0
    failed = 0

    export_extension = (
        "."
        + template["export_format"]
        .lower()
        .lstrip(".")
    )

    section("Rendering Icons")

    # Step 7 - Render every icon
    for index, png_file in enumerate(
        png_files,
        start=1
    ):

        output_file = (
            ICONS_FOLDER
            / f"{png_file.stem}{export_extension}"
        )

        # Skip icons already rendered
        if output_file.exists():

            skipped += 1

            progress(
                index,
                total,
                f"Skipped: {output_file.name}",
                "warning"
            )

            continue

        try:

            render_successful = render_icon(
                template,
                png_file,
                output_file
            )

            if render_successful:

                rendered += 1

                progress(
                    index,
                    total,
                    f"Saved: {output_file.name}",
                    "success"
                )

            else:

                failed += 1

                progress(
                    index,
                    total,
                    f"Failed: {png_file.name}",
                    "error"
                )

        except Exception as render_error:

            failed += 1

            progress(
                index,
                total,
                f"Failed: {png_file.name}",
                "error"
            )

            print(
                f"    Reason: {render_error}"
            )

    elapsed_time = (
        perf_counter()
        - build_start_time
    )

    build_summary(
        template_name=template["name"],
        total=total,
        rendered=rendered,
        skipped=skipped,
        failed=failed,
        elapsed_time=format_elapsed_time(
            elapsed_time
        ),
        output_folder=ICONS_FOLDER
    )


if __name__ == "__main__":
    build_icons()