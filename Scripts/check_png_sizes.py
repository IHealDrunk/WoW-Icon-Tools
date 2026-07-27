from PIL import Image
import os
from collections import Counter

folder = r"C:\Users\jstme\OneDrive\Documents\WoW Icon Project\Orginial BLP"

sizes = Counter()
total = 0

for file in os.listdir(folder):
    if file.lower().endswith(".blp"):
        path = os.path.join(folder, file)

        try:
            with Image.open(path) as img:
                sizes[img.size] += 1
                total += 1

        except Exception as e:
            print(f"Error reading {file}: {e}")

print(f"\nChecked {total} BLP files\n")

for size, count in sizes.items():
    print(f"{size}: {count} files")