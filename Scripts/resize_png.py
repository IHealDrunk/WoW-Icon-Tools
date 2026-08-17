from PIL import Image

from utils import (
    PNG_FOLDER,
    RESIZED_FOLDER,
    REVIEW_FOLDER,
)


# Crop settings
CROP_BOX = (
    6,
    6,
    122,
    122
)


def resize_icons():

    print("Starting PNG resize...")
    print()

    processed = 0
    skipped = 0
    review = 0
    errors = 0

    # Find all PNG files including subfolders
    png_files = list(
        PNG_FOLDER.rglob("*.png")
    )

    print(f"Found {len(png_files)} PNG files")
    print()

    for png_file in png_files:

        try:

            # Preserve folder structure
            relative_path = png_file.relative_to(
                PNG_FOLDER
            )

            output_file = (
                RESIZED_FOLDER /
                relative_path
            )

            review_file = (
                REVIEW_FOLDER /
                relative_path
            )

            # Open image
            with Image.open(png_file) as img:

                img = img.convert("RGBA")

                original_size = img.size

                # -----------------------------------
                # Send non-64x64 images to REVIEW
                # -----------------------------------

                if original_size != (64, 64):

                    review_file.parent.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    # Only create review copy if missing
                    if not review_file.exists():

                        img.save(
                            review_file,
                            "PNG"
                        )

                    review += 1

                    print(
                        f"[REVIEW] {png_file.name} "
                        f"({original_size[0]}x{original_size[1]})"
                    )

                    continue

                # -----------------------------------
                # Skip files already resized
                # -----------------------------------

                output_file.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                if output_file.exists():

                    skipped += 1

                    print(
                        f"[SKIPPED] {png_file.name}"
                    )

                    continue

                # -----------------------------------
                # Resize standard 64x64 WoW icon
                # -----------------------------------

                print(
                    f"[OK] Resizing: {png_file.name}"
                )

                # Upscale to 128x128
                img = img.resize(
                    (128, 128),
                    Image.Resampling.LANCZOS
                )

                # Remove transparent edge
                img = img.crop(
                    CROP_BOX
                )

                # Restore final 128x128 size
                img = img.resize(
                    (128, 128),
                    Image.Resampling.LANCZOS
                )

                # Save PNG
                img.save(
                    output_file,
                    "PNG"
                )

            processed += 1

        except Exception as e:

            errors += 1

            print(
                f"[FAILED] {png_file.name}"
            )

            print(e)

    print()
    print("===================================")
    print("Resize Complete")
    print("===================================")
    print(f"Processed:          {processed}")
    print(f"Already processed:  {skipped}")
    print(f"Needs review:       {review}")
    print(f"Errors:             {errors}")
    print("===================================")


if __name__ == "__main__":
    resize_icons()