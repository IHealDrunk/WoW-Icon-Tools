import json
import subprocess
from pathlib import Path


# ==========================================================
# Project Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).parent.parent

TEMPLATES_FOLDER = PROJECT_ROOT / "Templates"


def find_gimp() -> Path:
    """
    Locate the GIMP console executable.

    Returns:
        The path to the GIMP console executable.

    Raises:
        FileNotFoundError if GIMP cannot be located.
    """

    possible_locations = [
        Path(
            r"C:\Program Files\GIMP 3\bin\gimp-console-3.exe"
        ),
        Path(
            r"C:\Program Files (x86)\GIMP 3\bin\gimp-console-3.exe"
        ),
        (
            Path.home()
            / "AppData"
            / "Local"
            / "Programs"
            / "GIMP 3"
            / "bin"
            / "gimp-console-3.exe"
        ),
    ]

    for location in possible_locations:
        if location.exists():
            return location

    raise FileNotFoundError(
        "GIMP 3 could not be located.\n"
        "Please install GIMP 3."
    )


GIMP_EXE = find_gimp()


# ==========================================================
# Utility Functions
# ==========================================================

def escape_script_fu_string(value: str) -> str:
    """
    Escape a Python string so it can safely be placed inside
    a Script-Fu string.
    """

    return (
        value
        .replace("\\", "/")
        .replace('"', '\\"')
    )


def get_gimp_error_output(
    result: subprocess.CompletedProcess
) -> str:
    """
    Return the most useful output from a failed GIMP command.
    """

    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()

    if stderr:
        return stderr

    if stdout:
        return stdout

    return (
        "GIMP did not provide any additional "
        "error information."
    )


# ==========================================================
# Template Loading
# ==========================================================

def load_template_settings(template_name: str):
    """
    Load template.json for the selected template.
    """

    template_folder = TEMPLATES_FOLDER / template_name
    settings_file = template_folder / "template.json"

    if not template_folder.exists():
        print("ERROR: Template folder was not found:")
        print(template_folder)
        return None

    if not settings_file.exists():
        print("ERROR: template.json was not found:")
        print(settings_file)
        return None

    try:
        with open(
            settings_file,
            "r",
            encoding="utf-8"
        ) as file:
            settings = json.load(file)

    except json.JSONDecodeError as error:
        print("ERROR: template.json contains invalid JSON.")
        print(error)
        return None

    required_fields = [
        "name",
        "template_file",
        "replace_layer",
        "icon_size",
        "export_format",
    ]

    for field in required_fields:
        if field not in settings:
            print(
                f"ERROR: Missing template setting: {field}"
            )
            return None

    settings["template_folder"] = template_folder
    settings["template_path"] = (
        template_folder
        / settings["template_file"]
    )

    if not settings["template_path"].exists():
        print("ERROR: GIMP template file was not found:")
        print(settings["template_path"])
        return None

    return settings


# ==========================================================
# Template Validation
# ==========================================================

def make_layer_test_command(
    template_path: Path,
    replace_layer_name: str,
) -> str:
    """
    Create a Script-Fu command that checks whether the
    configured replacement layer exists inside the selected
    GIMP template.
    """

    template_path_text = escape_script_fu_string(
        str(template_path.resolve())
    )

    layer_name_text = escape_script_fu_string(
        replace_layer_name
    )

    return f"""
(script-fu-use-v3)

(let*
    (
        (image
            (gimp-file-load
                RUN-NONINTERACTIVE
                "{template_path_text}"
            )
        )

        (layers
            (gimp-image-get-layers image)
        )

        (layer-count
            (vector-length layers)
        )

        (replace-layer-found FALSE)
    )

    (do
        (
            (index 0 (+ index 1))
        )

        (
            (= index layer-count)
        )

        (let*
            (
                (layer
                    (vector-ref layers index)
                )

                (layer-name
                    (gimp-item-get-name layer)
                )
            )

            (if
                (string=? layer-name "{layer_name_text}")

                (set! replace-layer-found TRUE)
            )
        )
    )

    (if
        (not replace-layer-found)

        (error
            "Configured replacement layer was not found"
        )
    )

    (gimp-image-delete image)
)
"""


def validate_template(
    settings: dict
) -> tuple[bool, str | None]:
    """
    Ask GIMP to open the selected template and verify that the
    configured replacement layer exists.

    Returns:
        A tuple containing:
        - True and None when validation passes.
        - False and an error message when validation fails.
    """

    template_path = settings["template_path"]
    replace_layer_name = settings["replace_layer"]

    script_fu_command = make_layer_test_command(
        template_path,
        replace_layer_name,
    )

    command = [
        str(GIMP_EXE),
        "--no-interface",
        "--batch-interpreter=plug-in-script-fu-eval",
        f"--batch={script_fu_command}",
        "--quit",
    ]

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

    except OSError as error:
        return (
            False,
            f"GIMP could not be started: {error}"
        )

    if result.returncode != 0:
        gimp_output = get_gimp_error_output(result)

        return (
            False,
            (
                f'Layer "{replace_layer_name}" was not '
                "found inside the template.\n"
                f"{gimp_output}"
            )
        )

    return True, None


# ==========================================================
# Rendering Command
# ==========================================================

def make_render_command(
    template_path: Path,
    input_icon: Path,
    output_icon: Path,
    replace_layer_name: str,
) -> str:
    """
    Build the Script-Fu command that renders one icon.
    """

    template_path_text = escape_script_fu_string(
        str(template_path.resolve())
    )

    input_icon_text = escape_script_fu_string(
        str(input_icon.resolve())
    )

    output_icon_text = escape_script_fu_string(
        str(output_icon.resolve())
    )

    layer_name_text = escape_script_fu_string(
        replace_layer_name
    )

    return f"""
(script-fu-use-v3)

(let*
    (
        ; Open a fresh copy of the master template.
        (image
            (gimp-file-load
                RUN-NONINTERACTIVE
                "{template_path_text}"
            )
        )

        ; Read the template's root layer stack.
        (layers
            (gimp-image-get-layers image)
        )

        (layer-count
            (vector-length layers)
        )

        ; Variables used while searching for the placeholder.
        (placeholder-layer -1)
        (placeholder-position -1)
    )

    ; Find the configured placeholder layer and remember
    ; its exact position in the layer stack.
    (do
        (
            (index 0 (+ index 1))
        )

        (
            (= index layer-count)
        )

        (let*
            (
                (current-layer
                    (vector-ref layers index)
                )

                (current-layer-name
                    (gimp-item-get-name current-layer)
                )
            )

            (if
                (string=?
                    current-layer-name
                    "{layer_name_text}"
                )

                (begin
                    (set!
                        placeholder-layer
                        current-layer
                    )

                    (set!
                        placeholder-position
                        index
                    )
                )
            )
        )
    )

    ; Stop immediately if the configured layer is missing.
    (if
        (= placeholder-position -1)

        (error
            "Configured replacement layer was not found"
        )
    )

    ; Load the new PNG as a layer belonging to the template.
    (let*
        (
            (new-icon-layer
                (gimp-file-load-layer
                    RUN-NONINTERACTIVE
                    image
                    "{input_icon_text}"
                )
            )
        )

        ; Insert the imported icon into the exact location
        ; occupied by the transparent placeholder.
        (gimp-image-insert-layer
            image
            new-icon-layer
            -1
            placeholder-position
        )

        ; Give it the configured layer name.
        (gimp-item-set-name
            new-icon-layer
            "{layer_name_text}"
        )

        ; Remove the old transparent placeholder.
        (gimp-image-remove-layer
            image
            placeholder-layer
        )

        ; Export using the extension in the output filename.
        (gimp-file-save
            RUN-NONINTERACTIVE
            image
            "{output_icon_text}"
            -1
        )
    )

    ; Close the temporary image without saving over the XCF.
    (gimp-image-delete image)
)
"""


# ==========================================================
# Icon Rendering
# ==========================================================

def render_icon(
    template_settings: dict,
    input_icon: Path,
    output_icon: Path,
) -> bool:
    """
    Render a single icon through GIMP.

    Successful GIMP output is hidden. Failure details are
    raised so build_icon.py can display them cleanly.
    """

    input_icon = Path(input_icon)
    output_icon = Path(output_icon)

    if not input_icon.exists():
        raise FileNotFoundError(
            f"Input icon was not found: {input_icon}"
        )

    expected_extension = (
        "."
        + template_settings["export_format"]
        .lower()
        .lstrip(".")
    )

    if output_icon.suffix.lower() != expected_extension:
        raise ValueError(
            "Output extension does not match template.json. "
            f"Expected {expected_extension}, "
            f"received {output_icon.suffix}."
        )

    output_icon.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    script_fu_command = make_render_command(
        template_path=template_settings["template_path"],
        input_icon=input_icon,
        output_icon=output_icon,
        replace_layer_name=template_settings["replace_layer"],
    )

    command = [
        str(GIMP_EXE),
        "--no-interface",
        "--batch-interpreter=plug-in-script-fu-eval",
        f"--batch={script_fu_command}",
        "--quit",
    ]

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

    except OSError as error:
        raise RuntimeError(
            f"GIMP could not be started: {error}"
        ) from error

    if result.returncode != 0:
        gimp_output = get_gimp_error_output(result)

        raise RuntimeError(
            "GIMP failed to render the icon.\n"
            f"{gimp_output}"
        )

    if not output_icon.exists():
        raise RuntimeError(
            "GIMP completed, but no output file was created."
        )

    return True