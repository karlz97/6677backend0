import csv
import requests
import os
import argparse
from typing import List, Set
from datetime import datetime

# Default API endpoint
DEFAULT_API_URL = "http://localhost:8000"
ADD_AUDIO_META_ENDPOINT = "/add-audio-meta"

# Log file for processed files
PROCESSED_FILES_LOG = "processed_files.log"


def load_processed_files() -> Set[str]:
    if os.path.exists(PROCESSED_FILES_LOG):
        with open(PROCESSED_FILES_LOG, "r") as f:
            return set(f.read().splitlines())
    return set()


def log_processed_file(filename: str):
    with open(PROCESSED_FILES_LOG, "a") as f:
        f.write(f"{filename}\n")


def process_csv_file(file_path: str):
    with open(file_path, "r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
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
                "created_at": datetime.utcnow().isoformat(),  # Assuming you want to set the current time
            }

            response = requests.post(ADD_AUDIO_META_ENDPOINT, json=audio_meta)

            if response.status_code == 200:
                print(f"Successfully added audio metadata for {row['Source_id']}")
            else:
                print(
                    f"Failed to add audio metadata for {row['Source_id']}. Status code: {response.status_code}"
                )
                print(f"Response: {response.text}")


def process_folder(folder_path: str):
    processed_files = load_processed_files()

    for filename in os.listdir(folder_path):
        if filename.endswith(".csv") and filename not in processed_files:
            file_path = os.path.join(folder_path, filename)
            print(f"Processing file: {filename}")
            process_csv_file(file_path)
            log_processed_file(filename)
            print(f"Completed processing: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Process CSV files and upload audio metadata to the server.",
        epilog="Example usage:\n"
        "  python batch_post.py.py data.input/book1.csv\n"
        "  python batch_post.py.py data.input/\n"
        "  python batch_post.py.py -u http://api.example.com data.input/book1.csv",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        help="Path to a CSV file or a folder containing CSV files. "
        "If a folder is specified, all new CSV files in the folder will be processed.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "-u",
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Specify the API URL (default: {DEFAULT_API_URL})",
    )
    args = parser.parse_args()

    path = args.path
    api_url = args.api_url

    global ADD_AUDIO_META_ENDPOINT
    ADD_AUDIO_META_ENDPOINT = f"{api_url}{ADD_AUDIO_META_ENDPOINT}"

    if args.verbose:
        print(f"Using API URL: {api_url}")

    if os.path.isfile(path):
        if path.endswith(".csv"):
            process_csv_file(path)
            print(f"Processed single file: {path}")
        else:
            print("Error: The specified file is not a CSV file.")
    elif os.path.isdir(path):
        process_folder(path)
        print(f"Processed all new CSV files in folder: {path}")
    else:
        print("Error: The specified path does not exist.")


if __name__ == "__main__":
    main()
