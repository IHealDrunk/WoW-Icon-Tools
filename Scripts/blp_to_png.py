from pathlib import Path
from PIL import Image
import blp

# Folders
input_folder = Path(r"C:\Users\jstme\OneDrive\Documents\WoW Icon Project\02_BLP")
output_folder = Path(r"C:\Users\jstme\OneDrive\Documents\WoW Icon Project\03_Converted PNG")

output_folder.mkdir(exist_ok=True)

converted = 0
failed = 0

print("Starting conversion...\n")

for blp_file in input_folder.rglob("*.blp"):

    try:
        # Keep the same folder structure
        relative_path = blp_file.relative_to(input_folder)

        output_file = output_folder / relative_path.with_suffix(".png")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert
        img = Image.open(blp_file)
        img.save(output_file)

        converted += 1

        print(f"[OK] {converted}: {blp_file.name}")

    except Exception as e:
        failed += 1
        print(f"[FAILED] {blp_file.name}")
        print(e)

print("\n==========================")
print("Conversion Complete")
print(f"Converted: {converted}")
print(f"Failed: {failed}")
print("==========================")