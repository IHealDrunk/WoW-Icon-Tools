APP_NAME = "WoW Icon Tools"
APP_VERSION = "1.0.0"

HEADER_WIDTH = 50
PROGRESS_BAR_WIDTH = 30


def line(character: str = "=") -> None:
    """
    Print a full-width divider line.
    """

    print(character * HEADER_WIDTH)


def app_header() -> None:
    """
    Print the main application header.
    """

    print()
    line()
    print(f" {APP_NAME} v{APP_VERSION}")
    line()
    print()


def section(title: str) -> None:
    """
    Print a section heading.
    """

    print()
    line("-")
    print(title)
    line("-")


def success(message: str) -> None:
    """
    Print a success message.
    """

    print(f"✓ {message}")


def info(message: str) -> None:
    """
    Print an information message.
    """

    print(f"ℹ {message}")


def warning(message: str) -> None:
    """
    Print a warning message.
    """

    print(f"⚠ {message}")


def error(message: str) -> None:
    """
    Print an error message.
    """

    print(f"✗ {message}")


def progress(
    current: int,
    total: int,
    message: str,
    status: str | None = None
) -> None:
    """
    Display a single-line progress bar.

    Example:
    [███████████████░░░░░░░░░░░░░░░] 50.0%  50/100  ✓ Saved: Fireball.tga
    """

    if total <= 0:
        return

    # Calculate completion percentage
    ratio = min(
        max(current / total, 0),
        1
    )

    percentage = ratio * 100


    # Calculate progress bar
    filled_length = int(
        PROGRESS_BAR_WIDTH * ratio
    )

    empty_length = (
        PROGRESS_BAR_WIDTH - filled_length
    )

    bar = (
        "█" * filled_length
        + "░" * empty_length
    )


    # Choose status symbol
    if status == "success":
        symbol = "✓"

    elif status == "warning":
        symbol = "⚠"

    elif status == "error":
        symbol = "✗"

    else:
        symbol = "•"


    # Build progress line
    progress_line = (
        f"[{bar}] "
        f"{percentage:5.1f}%  "
        f"{current}/{total}  "
        f"{symbol} {message}"
    )


    # Update the same console line
    print(
        f"\r{progress_line}\033[K",
        end="",
        flush=True
    )


    # Move to a new line when complete
    if current >= total:
        print()


def labeled_value(
    label: str,
    value,
    width: int = 18
) -> None:
    """
    Print a label and value using dotted spacing.

    Example:
    Rendered......... 100
    """

    dots = "." * max(
        2,
        width - len(label)
    )

    print(f"{label}{dots} {value}")


def build_summary(
    template_name: str,
    total: int,
    rendered: int,
    skipped: int,
    failed: int,
    elapsed_time: str,
    output_folder
) -> None:
    """
    Print the final build summary.
    """

    print()
    line()
    print("Build Complete")
    line()
    print()

    labeled_value(
        "Template",
        template_name
    )

    labeled_value(
        "Total",
        total
    )

    labeled_value(
        "Rendered",
        rendered
    )

    labeled_value(
        "Skipped",
        skipped
    )

    labeled_value(
        "Failed",
        failed
    )

    print()

    labeled_value(
        "Elapsed Time",
        elapsed_time
    )

    labeled_value(
        "Output",
        output_folder
    )

    print()

    if failed == 0:
        success("Build completed successfully!")
    else:
        warning(
            f"Build completed with {failed} error(s)."
        )

    print()
    print(f"Thank you for using {APP_NAME}!")
    line()