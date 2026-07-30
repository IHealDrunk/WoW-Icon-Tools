from PIL import Image

from utils import BLP_FOLDER, PNG_FOLDER


def convert_blp_to_png():

    converted = 0
    skipped = 0
    failed = 0

    print("Starting BLP conversion...")
    print()

    for blp_file in BLP_FOLDER.rglob("*.blp"):

        try:

            # Keep folder structure
            relative_path = blp_file.relative_to(
                BLP_FOLDER
            )

            output_file = (
                PNG_FOLDER /
                relative_path.with_suffix(".png")
            )

            output_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # Skip files already converted
            if output_file.exists():

                skipped += 1

                print(
                    f"[SKIPPED] {blp_file.name}"
                )

                continue

            # Convert BLP to PNG
            with Image.open(blp_file) as img:

                img.convert("RGBA").save(
                    output_file,
                    "PNG"
                )

            converted += 1

            print(
                f"[OK] {converted}: {blp_file.name}"
            )

        except Exception as e:

            failed += 1

            print(
                f"[FAILED] {blp_file.name}"
            )

            print(e)

    print()
    print("==========================")
    print("Conversion Complete")
    print("==========================")
    print(f"Converted: {converted}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {failed}")
    print("==========================")


if __name__ == "__main__":
    convert_blp_to_png()