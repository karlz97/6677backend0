import csv
import argparse

# Define base URLs
audio_base_url = "https://shortaudio.oss-cn-chengdu.aliyuncs.com/音频/"
image_base_url = "https://shortaudio.oss-cn-chengdu.aliyuncs.com/图片/"

# Set up argument parser
parser = argparse.ArgumentParser(
    description="Update URLs in a CSV file.",
    epilog="Example usage: python update_urls.py path/to/yourfile.csv",
)
parser.add_argument("csv_file", help="The path to the CSV file to be processed.")
args = parser.parse_args()

# Read the CSV file
with open(args.csv_file, mode="r", encoding="utf-8") as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)

# Update the URLs
for row in rows:
    if row["Audio_url"]:
        row["Audio_url"] = audio_base_url + row["Audio_url"]
    if row["Image_url"] and row["Image_url"] != "Null":
        row["Image_url"] = image_base_url + row["Image_url"]

# Write the updated data back to the CSV file
with open(args.csv_file, mode="w", encoding="utf-8", newline="") as outfile:
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("URLs updated successfully.")
