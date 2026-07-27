from PIL import Image
import os


input_folder = r"C:\Users\jstme\OneDrive\Documents\WoW Icon Project\03_Converted PNG"
output_folder = r"C:\Users\jstme\OneDrive\Documents\WoW Icon Project\04_ICON 128x128"


os.makedirs(output_folder, exist_ok=True)


# Statistics
total_files = 0
processed_count = 0
skipped_count = 0
error_count = 0


for filename in os.listdir(input_folder):

    total_files += 1

    if filename.lower().endswith((".png", ".tga")):

        input_path = os.path.join(input_folder, filename)

        try:
            img = Image.open(input_path).convert("RGBA")

            # Only process 64x64 icons
            if img.size == (64, 64):

                # Upscale to 128x128
                img = img.resize(
                    (128, 128),
                    Image.Resampling.LANCZOS
                )

                # Remove 6 pixels from each edge
                img = img.crop(
                    (6, 6, 122, 122)
                )

                # Resize back to 128x128
                img = img.resize(
                    (128, 128),
                    Image.Resampling.LANCZOS
                )

                output_path = os.path.join(
                    output_folder,
                    filename.replace(".tga", ".png")
                )

                img.save(output_path)

                processed_count += 1
                print(f"Processed: {filename}")

            else:
                skipped_count += 1
                print(f"Skipped {filename} - size is {img.size}")


        except Exception as e:
            error_count += 1
            print(f"Error processing {filename}: {e}")


print("\n===================================")
print("Icon Resize Complete")
print("===================================")

print(f"Total files checked: {total_files}")
print(f"Processed:           {processed_count}")
print(f"Skipped:             {skipped_count}")
print(f"Errors:              {error_count}")

print("===================================")