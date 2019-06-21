#!/usr/bin/env python3
# coding: utf-8
# main.py

import json
import requests
import time

class DiscogsReleaseGetter(object):
    def __init__(self):
        # set base url
        self.base_url = "http://api.discogs.com"

        # load user token
        config_file = open("login_info.json", "r", encoding="utf-8")
        login_data = json.load(config_file)
        self.user_token = login_data["user_token"]
        
        self.labels = []

    def create_label(self, label_id, name, profile, url, releases):
        label = {
            "id": label_id,
            "name": name,
            "profile": profile,
            "url": url,
            "releases": releases
        }

        return label

    def create_release(self, release_id, title, year, genres,
                       styles, formats, artists, tracks, rating):
        release = {
            "id": release_id,
            "title": title,
            "year": year,
            "genres": genres,
            "styles": styles,
            "formats": formats,
            "artists": artists,
            "tracks": tracks,
            "rating": rating
        }
        
        return release

    def fetch(self, method, url, base_url=True):
        url = self.base_url + url if base_url else url
        resp = requests.request(method, url, params={"token": self.user_token})

        if resp.status_code == 204:
            return resp, None
        
        body = json.loads(resp.content.decode("utf8"))

        if not (200 <= resp.status_code < 300):
            print("HTTP Error {0}: {1}".format(body["message"], resp.status_code))
            return resp, None

        return resp, body

    def wait_if_necessary(self, resp):
        if int(resp.headers["X-Discogs-Ratelimit-Remaining"]) < 3:
            print("Waiting for 30s, the number of remaining requests is small")
            time.sleep(30)

    def collect_labels(self, label_ids):
        for label_id in label_ids:
            self.collect_label(label_id)
    
    def collect_label(self, label_id):
        url = "/labels/{0}".format(label_id)
        resp, body = self.fetch("GET", url)
        
        if body is None:
            return

        label_id = body["id"]
        label_name = body["name"]
        label_profile = body["profile"]
        label_url = body["uri"]

        print("[label] id: {0}".format(label_id))
        print("[label] name: {0}".format(label_name))
        print("[label] profile: {0}".format(label_profile))
        print("[label] url: {0}".format(label_url))

        label_releases = self.collect_releases(label_id)

        if label_releases is not None:
            label = self.create_label(label_id, label_name, label_profile,
                                      label_url, label_releases)
            self.labels.append(label)

    def collect_releases(self, label_id):
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
        
            if "next" not in body["pagination"]["urls"]:
                break

            url = body["pagination"]["urls"]["next"]
            
            for i, release in enumerate(body["releases"]):
                release = self.collect_release(release["id"])

                if release is not None:
                    releases.append(release)
        
        return releases
    
    def collect_release(self, release_id):
        url = "/releases/{0}".format(release_id)
        resp, body = self.fetch("GET", url)

        if body is None:
            return None
        
        self.wait_if_necessary(resp)
        
        release_id = body["id"]
        title = body["title"]
        year = body["year"]
        genres = body["genres"]
        styles = body["styles"]
        formats = body["formats"]
        artists = self.prettify_artists(body["artists"])
        tracks = self.prettify_tracks(body["tracklist"])

        rating = 5.0

        return self.create_release(release_id, title, year, genres,
                                   styles, formats, artists, tracks, rating)

    def prettify_artists(self, result_artists):
        artists = []

        for i, artist_data in enumerate(result_artists):
            artist = {}

            artist["id"] = artist_data["id"]
            artist["name"] = artist_data["name"]

            artists.append(artist)

        return artists
    
    def prettify_tracks(self, result_tracks):
        tracks = []

        for i, track_data in enumerate(result_tracks):
            track = {}

            track["position"] = track_data["position"]
            track["title"] = track_data["title"]

            if track_data["duration"] != "":
                minutes, seconds = track_data["duration"].split(":")
                minutes, seconds = int(minutes), int(seconds)
                track["duration"] = minutes * 60 + seconds

            tracks.append(track)
        
        return tracks

def main():
    release_getter = DiscogsReleaseGetter()
    release_getter.collect_labels([16463])

if __name__ == "__main__":
    main()

