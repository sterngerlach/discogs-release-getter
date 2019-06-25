#!/usr/bin/env python3
# coding: utf-8
# main.py

import json
import requests
import sys
import time
import traceback

class DiscogsReleaseGetter(object):
    def __init__(self):
        # set base url
        self.base_url = "http://api.discogs.com"

        # load user token
        config_file = open("login_info.json", "r", encoding="utf-8")
        login_data = json.load(config_file)
        self.user_token = login_data["user_token"]
        config_file.close()

    def fetch(self, method, url, base_url=True):
        url = self.base_url + url if base_url else url
        print("fetch(): url: {0}".format(url))
        resp = requests.request(method, url,
                                params={"token": self.user_token})

        if resp.status_code == 204:
            return resp, None

        if not (200 <= resp.status_code < 300):
            print("HTTP Error {0}".format(resp.status_code))
            return resp, None
        
        try:
            body = json.loads(resp.content.decode("utf8"))
        except Exception as e:
            traceback.print_exc()
            return resp, None

        return resp, body

    def wait_if_necessary(self, resp):
        if int(resp.headers["X-Discogs-Ratelimit-Remaining"]) < 5:
            print("Waiting for 30s, the number of remaining requests is small")
            time.sleep(30)

    def dump_json(self, label_id, label, releases):
        label["releases"] = releases

        file_name = "label_{0}.json".format(label_id)
        label_file = open(file_name, "w", encoding="utf-8")
        json.dump([label], label_file, ensure_ascii=False, indent=4,
                  sort_keys=False, separators=(",", ": "))
        label_file.close()

    def collect_label(self, label_id):
        url = "/labels/{0}".format(label_id)
        resp, body = self.fetch("GET", url)
        
        if body is None:
            return

        label = {}
        label["id"] = body["id"]
        label["name"] = body["name"].strip()
        label["profile"] = body["profile"].strip()
        label["url"] = body["uri"].strip()

        print("[label] id: {0}".format(label["id"]))
        print("[label] name: {0}".format(label["name"]))
        print("[label] profile: {0}".format(label["profile"]))
        print("[label] url: {0}".format(label["url"]))
        
        self.collect_releases(label_id, label)

    def collect_releases(self, label_id, label):
        releases = []
        page = 0
        per_page = 75

        url = self.base_url + "/labels/{0}/releases?page={1}&per_page={2}"
        url = url.format(label_id, page, per_page)

        while True:
            resp, body = self.fetch("GET", url, base_url=False)

            if body is None:
                break

            self.wait_if_necessary(resp)
            
            for i, release in enumerate(body["releases"]):
                release = self.collect_release(release["id"])

                if release is not None:
                    releases.append(release)

            self.dump_json(label_id, label, releases)
            
            if "next" not in body["pagination"]["urls"]:
                break

            page += 1
            url = self.base_url + "/labels/{0}/releases?page={1}&per_page={2}"
            url = url.format(label_id, page, per_page)
    
    def collect_release(self, release_id):
        url = "/releases/{0}".format(release_id)
        resp, body = self.fetch("GET", url)

        if body is None:
            return None
        
        self.wait_if_necessary(resp)

        release = {}
        
        release["id"] = body["id"]
        release["title"] = body["title"].strip()
        release["year"] = body["year"]

        if "genres" in body:
            release["genres"] = body["genres"]
        
        if "formats" in body and len(body["formats"]) > 0:
            release["format"] = self.prettify_formats(body["formats"])

        release["artists"] = self.prettify_artists(body["artists"])
        release["tracks"] = self.prettify_tracks(body["tracklist"])
        release["rating_count"], release["rating"] = \
            self.get_release_rating(release_id)
        
        print("[release] id: {0}, title: {1}, year: {2}"
              .format(release["id"], release["title"], release["year"]))
        print("[release] rating_count: {0}, rating_average: {1}"
              .format(release["rating_count"], release["rating"]))

        return release

    def prettify_formats(self, result_formats):
        prettify_format = {}

        if "descriptions" in result_formats[0]:
            prettify_format["descriptions"] = result_formats[0]["descriptions"]

        if "name" in result_formats[0]:
            prettify_format["name"] = result_formats[0]["name"]

        return prettify_format

    def prettify_artists(self, result_artists):
        artists = []

        for i, artist_data in enumerate(result_artists):
            artist = {}

            artist["id"] = artist_data["id"]
            artist["name"] = artist_data["name"].strip()

            artists.append(artist)

        return artists
    
    def prettify_tracks(self, result_tracks):
        tracks = []

        for i, track_data in enumerate(result_tracks):
            track = {}

            track["position"] = track_data["position"]
            track["title"] = track_data["title"].strip()

            if track_data["duration"] != "":
                times = track_data["duration"].strip().split(":")
                minutes, seconds = times[len(times) - 2], times[len(times) - 1]
                minutes, seconds = int(minutes), int(seconds)
                track["duration"] = minutes * 60 + seconds

            tracks.append(track)
        
        return tracks

    def get_release_rating(self, release_id):
        url = "/releases/{0}/rating".format(release_id)
        resp, body = self.fetch("GET", url)

        if body is None:
            return 0, 0.0

        self.wait_if_necessary(resp)

        return body["rating"]["count"], body["rating"]["average"]

def main():
    release_getter = DiscogsReleaseGetter()
    release_getter.collect_label(8184)

if __name__ == "__main__":
    main()

