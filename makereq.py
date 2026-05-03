import os

# Mapping the imports to their respective PyPI packages
# json, os, sys, random, and io are standard libraries (no install needed)
required_packages = [
    "requests",          # for 'import requests'
    "google-genai",      # for 'from google import genai'
    "pillow"             # for 'from PIL import Image'
]

# Ensure the level_0 directory exists
output_dir = "./level_0"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "requirements.txt")

with open(output_path, 'w') as f:
    for pkg in sorted(required_packages):
        f.write(f"{pkg}\n")

print(f"File created at: {output_path}")
print("Contents:")
for pkg in sorted(required_packages):
    print(f" - {pkg}")

