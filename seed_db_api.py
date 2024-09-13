import csv
import requests
import os

# API endpoint
API_URL = "http://localhost:8000"  # Change this to your actual API URL
ADD_AUDIO_META_ENDPOINT = f"{API_URL}/add-audio-meta"

# CSV file path
CSV_FILE = "data.input/book1.csv"


def process_csv_file(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Prepare the data for the API call
            audio_meta = {
                "src_id": row["Source_id"],
                "description": row["Title"],
                "audio_src": row["Audio_url"],
                "location": row["Location"],
                "images": [
                    img.strip() for img in row["Image_url"].split(",") if img.strip()
                ],
                "creator": row["Creator_id"],
                "tags": [tag.strip() for tag in row["Tag"].split(",")],
            }

            # Make the API call
            response = requests.post(ADD_AUDIO_META_ENDPOINT, json=audio_meta)

            if response.status_code == 200:
                print(f"Successfully added audio metadata for {row['Source_id']}")
            else:
                print(
                    f"Failed to add audio metadata for {row['Source_id']}. Status code: {response.status_code}"
                )
                print(f"Response: {response.text}")


if __name__ == "__main__":
    if not os.path.exists(CSV_FILE):
        print(f"Error: CSV file not found at {CSV_FILE}")
    else:
        process_csv_file(CSV_FILE)
        print("CSV processing completed.")
