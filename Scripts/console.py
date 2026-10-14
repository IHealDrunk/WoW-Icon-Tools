from time import perf_counter

APP_NAME = "WoW Icon Tools"
APP_VERSION = "1.3.0"

HEADER_WIDTH = 50
PROGRESS_BAR_WIDTH = 30
REMAINING_TIME_LABEL = "How much longer this shit will be"


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
    output_folder,
    known_bad: int = 0,
    review: int = 0,
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

    labeled_value("Needs Review", review)
    labeled_value("Known bad BLPs", known_bad)
    labeled_value("New failures", failed)

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

    if known_bad:
        warning(f'{known_bad} unchanged bad BLP(s) were skipped; '
                're-extract their sources to include them.')
    print()
    print(f"Thank you for using {APP_NAME}!")
    line()

def duration_text(seconds, include_seconds=False):
    seconds = max(0, int(seconds))
    hours, remaining = divmod(seconds, 3600)
    minutes, seconds = divmod(remaining, 60)
    if hours:
        text = f'{hours}h {minutes}m'
        return f'{text} {seconds}s' if include_seconds else text
    if minutes:
        return f'{minutes}m {seconds}s'
    return f'{seconds}s'


class StageProgress:
    """One progress layout with an adaptive time estimate for every stage."""
    def __init__(self, total, control=None):
        self.control = control
        self.paused_at_start = getattr(control, "paused_seconds", 0)
        self.work_paused_at_start = self.paused_at_start
        self.total = total
        self.last_update = 0.0
        self.started = perf_counter()
        self.work_total = None
        self.work_started = self.started

    def set_work_remaining(self, total):
        # Rendering starts after a scan of reusable files: estimate actual work,
        # rather than treating fast skips as representative GIMP renders.
        self.work_total = total
        self.work_started = perf_counter()
        self.work_paused_at_start = getattr(self.control, "paused_seconds", 0)
        self.last_update = 0.0

    def update(self, current, work_done=None, **counts):
        now = perf_counter()
        if now - self.last_update >= 0.1 or current == self.total:
            paused = getattr(self.control, 'paused_seconds', 0)
            elapsed = max(0, now - self.started - (paused - self.paused_at_start))
            work_elapsed = max(0, now - self.work_started - (paused - self.work_paused_at_start))
            if current >= self.total:
                eta = '0s'
            elif self.work_total is not None:
                eta = (duration_text(work_elapsed / work_done
                                     * (self.work_total - work_done))
                       if work_done else 'estimating')
            else:
                eta = (duration_text(elapsed / current * (self.total - current))
                       if current else 'estimating')
            message = f'Left: {self.total - current} | {REMAINING_TIME_LABEL}: {eta}'
            for label, value in counts.items():
                message += f" | {label.replace('_', ' ')}: {value}"
            progress(current, self.total, message)
            self.last_update = now
