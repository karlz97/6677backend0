import csv
import os
import json
from app.models import AudioMetadata

DATA_INPUT_DIR = "data.input"
ADDED_FILES_LOG = "added_files.log"


with open(DATA_INPUT_DIR + "/book1.csv", "r", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        print(row)

file = open("data.input/book1.csv", "r")
reader = csv.DictReader(file)
