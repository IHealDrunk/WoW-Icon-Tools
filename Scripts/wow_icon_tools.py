from gi.repository import Gimp, Gio
import os


# ==========================================================
#
# WoW Icon Tools
# Version 1.0.3
#
# Processes 128x128 WoW icons through the GIMP template
# and exports finished TGA icons.
#
# Resume Mode:
# Already exported TGA files are skipped automatically.
#
# ==========================================================


# -------------------------
# Configuration
# -------------------------

INPUT_FOLDER = r"C:\Users\jstme\OneDrive\Documents\WoW Icon Project\04_ICON 128x128"

OUTPUT_FOLDER = r"C:\Users\jstme\OneDrive\Documents\WoW Icon Project\ICONS"

TEMPLATE_NAME = "Master GIMP Template.xcf"

EXPORT_EXTENSION = ".tga"


# -------------------------
# Statistics
# -------------------------

total_files = 0
processed_count = 0
skipped_count = 0
error_count = 0


def get_template():
    for img in Gimp.get_images():
        if TEMPLATE_NAME in img.get_name():
            return img

    return None


def replace_icon(icon_path):

    template = get_template()

    if template is None:
        print("Template not found")
        return None

    # Load icon
    file = Gio.File.new_for_path(icon_path)

    source_image = Gimp.file_load(
        Gimp.RunMode.NONINTERACTIVE,
        file
    )

    if source_image is None:
        print("Could not load:", icon_path)
        return None

    source_layer = source_image.get_layers()[0]

    # Create replacement layer
    new_icon = Gimp.Layer.new_from_drawable(
        source_layer,
        template
    )

    new_icon.set_name("ICON")

    # Find existing ICON layer
    old_icon = None
    icon_index = 0

    for i, layer in enumerate(template.get_layers()):
        if layer.get_name() == "ICON":
            old_icon = layer
            icon_index = i
            break

    # Remove old icon
    if old_icon:
        template.remove_layer(old_icon)

    # Insert new icon
    template.insert_layer(
        new_icon,
        None,
        icon_index
    )

    return template


def export_icon(template, output_path):

    output_file = Gio.File.new_for_path(output_path)

    Gimp.file_save(
        Gimp.RunMode.NONINTERACTIVE,
        template,
        output_file,
        None
    )


# =========================
# Batch Processing
# =========================

input_folder = INPUT_FOLDER
output_folder = OUTPUT_FOLDER

for filename in os.listdir(input_folder):

    if filename.lower().endswith(".png"):

        total_files += 1

        icon_path = os.path.join(
            input_folder,
            filename
        )

        output_filename = os.path.splitext(filename)[0] + EXPORT_EXTENSION

        output_path = os.path.join(
            output_folder,
            output_filename
        )

        # -------------------------
        # Resume Mode
        # -------------------------

        if os.path.exists(output_path):
            skipped_count += 1
            print(f"Skipping: {output_filename}")
            continue

        print("----------------------")
        print("Processing:", filename)

        try:

            template = replace_icon(icon_path)

            if template:

                export_icon(
                    template,
                    output_path
                )

                processed_count += 1

                print("Exported:", output_filename)

            else:
                error_count += 1

        except Exception as e:

            error_count += 1

            print("ERROR:", filename)
            print(e)


print("\n===================================")
print("WoW Icon Tools Summary")
print("===================================")

print(f"Total PNG files:      {total_files}")
print(f"Processed:            {processed_count}")
print(f"Skipped (existing):   {skipped_count}")
print(f"Errors:               {error_count}")

print("===================================")
print("Done!")