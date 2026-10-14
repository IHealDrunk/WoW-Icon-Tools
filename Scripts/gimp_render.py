import subprocess
import os
import tempfile
import time

from pathlib import Path

from utils import LOGS_FOLDER, atomic_write


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


GIMP_EXE = None  # Locate lazily so conversion/tests work without GIMP.


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
        str(GIMP_EXE or find_gimp()),
        "--new-instance",
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
            encoding="utf-8",
            errors="replace",
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
    use_loaded_template: bool = False,
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

    image_initializer = ('(gimp-image-duplicate wow-master-image)' if use_loaded_template
                         else f'(gimp-file-load RUN-NONINTERACTIVE "{template_path_text}")')

    return f"""
(script-fu-use-v3)

(let*
    (
        ; Open a fresh copy of the master template.
        (image
            {image_initializer}
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

def _render_icon(
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
        str(GIMP_EXE or find_gimp()),
        "--new-instance",
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
            encoding="utf-8",
            errors="replace",
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

def render_icon(template_settings, input_icon, output_icon):
    """Publish only a completed export; preserve the old file on failure."""
    atomic_write(output_icon, lambda temporary: _render_icon(
        template_settings, input_icon, temporary))
    return True


BATCH_SIZE = 32


def render_batch(template_settings, jobs, on_result, control=None):
    """Render (input, output) pairs with one GIMP and one loaded template.

    A closed receipt is written after each completed export. Only receipted
    outputs are published. Callbacks commit those files before polling controls;
    Save & Exit terminates only this isolated GIMP and discards unfinished work.
    """
    if not jobs:
        return
    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
    process = None
    temporary_outputs = []
    completed = set()
    try:
        with tempfile.TemporaryDirectory(prefix='.wow-batch-', dir=LOGS_FOLDER) as directory:
            scratch = Path(directory)
            commands = ['(script-fu-use-v3)',
                        '(define wow-master-image (gimp-file-load RUN-NONINTERACTIVE "'
                        + escape_script_fu_string(str(template_settings['template_path'].resolve()))
                        + '"))']
            receipts = []
            extension = '.' + template_settings['export_format'].lower().lstrip('.')
            for index, (source, output) in enumerate(jobs):
                source, output = Path(source), Path(output)
                if not source.is_file() or output.suffix.lower() != extension:
                    raise ValueError(f'Invalid render input/output: {source} -> {output}')
                output.parent.mkdir(parents=True, exist_ok=True)
                fd, filename = tempfile.mkstemp(prefix='.wow-', suffix=extension, dir=output.parent)
                os.close(fd)
                temporary = Path(filename)
                temporary_outputs.append(temporary)
                receipt = scratch / f'{index}.done'
                receipts.append(receipt)
                commands.append(make_render_command(template_settings['template_path'], source,
                                temporary, template_settings['replace_layer'], use_loaded_template=True))
                commands.append('(with-output-to-file "'
                                + escape_script_fu_string(str(receipt.resolve()))
                                + '" (lambda () (display "ok")))')
            commands.append('(gimp-image-delete wow-master-image)')
            script = scratch / 'batch.scm'
            script.write_text('\n'.join(commands), encoding='utf-8')
            log = scratch / 'gimp.log'
            command = [str(GIMP_EXE or find_gimp()), '--new-instance', '--no-interface',
                       '--batch-interpreter=plug-in-script-fu-eval',
                       '--batch=(load "' + escape_script_fu_string(str(script.resolve())) + '")', '--quit']
            def collect():
                for index, receipt in enumerate(receipts):
                    if index in completed or not receipt.is_file():
                        continue
                    # A partially written marker never counts as completion.
                    try:
                        if receipt.read_text(encoding='utf-8') != 'ok':
                            continue
                    except OSError:
                        continue
                    temporary = temporary_outputs[index]
                    source, output = jobs[index]
                    try:
                        if temporary.stat().st_size == 0:
                            continue
                        os.replace(temporary, output)
                    except OSError as exc:
                        completed.add(index)
                        on_result(source, output, f'Could not publish completed export: {exc}')
                    else:
                        completed.add(index)
                        on_result(source, output, None)
                    if control:
                        control.boundary()
            with log.open('wb') as stream:
                process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                           creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP
                                                          if os.name == 'nt' else 0))
                try:
                    while process.poll() is None:
                        collect()
                        if control:
                            control.boundary()
                        time.sleep(0.1)
                    collect()
                finally:
                    if process.poll() is None:
                        # Let the small active batch close its Script-Fu file and
                        # plug-ins normally. Killing only the launcher can orphan
                        # its children on Windows and leave temporary files locked.
                        print('\nFinishing the active GIMP batch before closing...')
                        try:
                            process.wait(timeout=30)
                        except subprocess.TimeoutExpired:
                            if os.name == 'nt':
                                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                               capture_output=True, check=False)
                            else:
                                process.kill()
                            process.wait(timeout=5)
            # A bad icon may abort a Script-Fu batch. Retry its uncompleted
            # peers individually so one failure cannot block the rest forever.
            for index, (source, output) in enumerate(jobs):
                if index in completed:
                    continue
                if control:
                    control.boundary()
                try:
                    render_icon(template_settings, source, output)
                except Exception as exc:
                    on_result(source, output, str(exc))
                else:
                    on_result(source, output, None)
    finally:
        for temporary in temporary_outputs:
            temporary.unlink(missing_ok=True)
