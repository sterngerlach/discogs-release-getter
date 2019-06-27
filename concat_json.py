#!/usr/bin/env python3
# coding: utf-8
# concat_json.py

import glob
import json

def main():
    json_files = glob.glob("datasets/label_[0-9]*.json")
    concat_data = []
    release_ids = []
    
    for file_name in json_files:
        label_file = open(file_name, "r", encoding="utf-8")
        label_data = json.load(label_file)[0]
        releases = []

        for release in label_data["releases"]:
            if release["id"] in release_ids:
                continue

            release_ids.append(release["id"])

            position = 1

            for track in release["tracks"]:
                track["position"] = position
                position += 1

            if release["rating_count"] == 0:
                del release["rating_count"]
                del release["rating"]

            releases.append(release)
        
        label_data["releases"] = releases
        concat_data.append(label_data)
        label_file.close()

    file_name = "datasets/label.json"
    label_file = open(file_name, "w", encoding="utf-8")
    json.dump(concat_data, label_file, ensure_ascii=False, indent=4,
              sort_keys=False, separators=(",", ": "))
    label_file.close()

if __name__ == "__main__":
    main()

