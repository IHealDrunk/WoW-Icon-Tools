APP_NAME = "WoW Icon Tools"
APP_VERSION = "1.0.0"

HEADER_WIDTH = 50


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
    Print a numbered progress message.

    Example:
    [1/100] ✓ Fireball.tga
    """

    prefix = f"[{current}/{total}]"

    if status == "success":
        print(f"{prefix} ✓ {message}")

    elif status == "warning":
        print(f"{prefix} ⚠ {message}")

    elif status == "error":
        print(f"{prefix} ✗ {message}")

    else:
        print(f"{prefix} {message}")


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
