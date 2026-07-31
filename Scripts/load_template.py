import json

from utils import TEMPLATES_FOLDER


def read_template_json(template_folder):
    """
    Read a template.json file and return its contents.

    Returns None if the file is missing or contains invalid JSON.
    """

    template_file = template_folder / "template.json"

    if not template_file.exists():
        return None

    try:
        with open(template_file, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        print("\nERROR: Invalid JSON found in:")
        print(template_file)
        print(error)
        return None

    except OSError as error:
        print("\nERROR: Could not read:")
        print(template_file)
        print(error)
        return None


def discover_templates():
    """
    Find valid template folders containing a readable template.json file.

    Each returned item contains:
    - folder_name
    - folder_path
    - template information from template.json
    """

    templates = []

    if not TEMPLATES_FOLDER.exists():
        print("ERROR: Templates folder not found:")
        print(TEMPLATES_FOLDER)
        return templates

    for template_folder in sorted(
        TEMPLATES_FOLDER.iterdir(),
        key=lambda folder: folder.name.lower(),
    ):
        if not template_folder.is_dir():
            continue

        template_info = read_template_json(template_folder)

        if template_info is None:
            continue

        templates.append(
            {
                "folder_name": template_folder.name,
                "folder_path": template_folder,
                "info": template_info,
            }
        )

    return templates


def select_template():
    """
    Display all discovered templates and let the user select one
    using its menu number.

    Returns the selected template folder name.
    """

    templates = discover_templates()

    if not templates:
        print("\nERROR: No valid templates were found.")
        print("Template folders must contain a valid template.json file.\n")
        print("Templates folder:")
        print(TEMPLATES_FOLDER)
        return None

    print("===================================")
    print("Available Templates")
    print("===================================")

    for number, template_data in enumerate(templates, start=1):
        info = template_data["info"]

        template_name = info.get(
            "name",
            template_data["folder_name"],
        )

        description = info.get("description")
        author = info.get("author")
        version = info.get("version")

        print(f"{number}. {template_name}")

        if description:
            print(f"   {description}")

        if author:
            print(f"   Author: {author}")

        if version:
            print(f"   Version: {version}")

        print()

    while True:
        selection = input("Select a template number: ").strip()

        try:
            selection_number = int(selection)

        except ValueError:
            print(f"Please enter a number from 1 to {len(templates)}.")
            continue

        if 1 <= selection_number <= len(templates):
            return templates[selection_number - 1]["folder_name"]

        print(f"Please select a number from 1 to {len(templates)}.")


def load_template(template_name):
    """
    Load and validate the selected template.

    Returns:
        template, template_folder

    Returns:
        None, None

    if validation fails.
    """

    template_folder = TEMPLATES_FOLDER / template_name
    template_file = template_folder / "template.json"

    if not template_folder.exists():
        print("\nERROR: Template folder not found:")
        print(template_folder)
        return None, None

    template = read_template_json(template_folder)

    if template is None:
        print("\nERROR: Template could not be loaded:")
        print(template_file)
        return None, None

    required_fields = [
        "name",
        "template_file",
        "replace_layer",
        "icon_size",
        "export_format",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in template
    ]

    if missing_fields:
        print("\nERROR: Template settings are missing:")

        for field in missing_fields:
            print(f"- {field}")

        print("\nTemplate file:")
        print(template_file)

        return None, None

    template_path = template_folder / template["template_file"]

    if not template_path.exists():
        print("\nERROR: GIMP template file not found:")
        print(template_path)
        return None, None

    icon_size = template["icon_size"]

    if not isinstance(icon_size, int) or icon_size <= 0:
        print("\nERROR: icon_size must be a positive whole number.")
        print(f"Current value: {icon_size}")
        return None, None

    export_format = template["export_format"]

    if not isinstance(export_format, str):
        print("\nERROR: export_format must be text.")
        print(f"Current value: {export_format}")
        return None, None

    if not export_format.startswith("."):
        template["export_format"] = f".{export_format}"

    preview_name = template.get("preview")

    if preview_name:
        template["preview_path"] = template_folder / preview_name

    template["template_path"] = template_path

    return template, template_folder