from PIL import Image

from utils import PNG_FOLDER, RESIZED_FOLDER


# Crop settings
CROP_BOX = (
    6,
    6,
    122,
    122,
)


def resize_icons():

    print("Starting PNG resize...\n")

    processed = 0
    skipped = 0
    errors = 0

    # Find all PNG files, including subfolders.
    png_files = list(PNG_FOLDER.rglob("*.png"))

    print(f"Found {len(png_files)} PNG files\n")

    for png_file in png_files:

        try:

            # Preserve the folder structure.
            relative_path = png_file.relative_to(PNG_FOLDER)
            output_file = RESIZED_FOLDER / relative_path

            output_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            # Skip files already resized.
            if output_file.exists():

                skipped += 1
                print(f"[SKIPPED] {png_file.name}")

                continue

            with Image.open(png_file) as img:

                img = img.convert("RGBA")

                # Only process original WoW 64x64 icons.
                if img.size != (64, 64):

                    skipped += 1
                    print(f"[SKIPPED] {png_file.name} ({img.size})")

                    continue

                print(f"[OK] Resizing: {png_file.name}")

                # Upscale, remove the transparent border,
                # then restore the final 128x128 size.
                img = img.resize(
                    (128, 128),
                    Image.Resampling.LANCZOS,
                )

                img = img.crop(CROP_BOX)

                img = img.resize(
                    (128, 128),
                    Image.Resampling.LANCZOS,
                )

                img.save(
                    output_file,
                    "PNG",
                )

            processed += 1

        except Exception as error:

            errors += 1

            print(f"[FAILED] {png_file.name}")
            print(error)

    print()
    print("===================================")
    print("Resize Complete")
    print("===================================")
    print(f"Processed: {processed}")
    print(f"Skipped:   {skipped}")
    print(f"Errors:    {errors}")
    print("===================================")


if __name__ == "__main__":
    resize_icons()