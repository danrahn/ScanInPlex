import argparse
import json
import os
import requests
import ScanInPlexCommon as Common
import subprocess
import urllib.parse

class Scanner:
    def __init__(self, cmd_args=None):
        self.valid = True
        self.cmd_args = cmd_args
        if self.cmd_args == None:
            parser = argparse.ArgumentParser()
            parser.add_argument('-d', '--directory')
            parser.add_argument('-r', '--refresh_metadata', action='store_true')
            self.cmd_args = parser.parse_args()

        if 'directory' not in self.cmd_args:
            self.valid = False
            return

        self.dir = self.cmd_args.directory
        self.refresh_metadata = self.cmd_args.refresh_metadata

    def process(self):
        """
        Attempts to scan/refresh the passed in library directory. Fails silently
        """

        if not self.valid:
            return
        config_file = Common.adjacent_file('config.json')
        if not os.path.exists(config_file):
            return

        config_string = ''
        with open(config_file, 'r') as f:
            config_string = ''.join(f.readlines())

        mappings = json.loads(config_string)
        section_id = -1
        section = None
        dir_lower = self.dir.lower()
        for section in mappings['sections']:
            for path in [p.lower() for p in section['paths']]:

                # Passed in directory must start with one our our root folders, but not make sure to ignore
                # partial matches (e.g. Z:\Movies2\SomeFolder compared to Z:\Movies)
                if dir_lower.startswith(path) and (len(dir_lower) == len(path) or dir_lower[len(path)] == '\\'):
                    section_id = section['section']
                    section = section
                    break
            if section_id != -1:
                break

        if section_id == -1:
            return

        if self.refresh_metadata:
            # refresh_metadata implies --web. Something's gone wrong if token/host aren't present, but ignore it
            self.refresh(section, mappings)
        else:
            self.scan(section_id, mappings)


    def scan(self, section_id, mappings):
        if 'token' in mappings and 'host' in mappings:
            token = mappings['token']
            host = mappings['host']
            webapi = f'{host}/library/sections/{section_id}/refresh?path={urllib.parse.quote(self.dir)}&X-Plex-Token={token}'
            result = requests.get(webapi).status_code
            if result == 200: # On error, fallback to the .exe
                return

        exe = mappings['exe']
        cmd = f'"{exe}" -s -c {section_id} -d "{self.dir}"'
        CREATE_NO_WINDOW = 0x08000000 # Don't show any output
        subprocess.call(cmd, creationflags=CREATE_NO_WINDOW)


    def refresh(self, section, mappings):
        """Refresh metadata for all items in the requested directory"""
        # Inefficient, but do the following:
        # 1: Get all items in a given library with the right type
        # 2: Parse all paths and build up list of metadata ids
        # 3: Make a request for each metadata id to refresh
        token = mappings['token']
        host = mappings['host']
        media_type = 1 # Default to refreshing individual movies
        refresh_key = 'ratingKey'
        if section['type'] == 'show':
            media_type = 4 # Refresh individual episodes
        elif section['type'] == 'artist':
            media_type = 10 # Refresh albums, but need to grab individual tracks to get file paths. This is slow.
            refresh_key = 'parentRatingKey'
        # Photo albums don't work. This should probably be filtered out during configuration.

        url = f'{host}/library/sections/{section["section"]}/all?type={media_type}&X-Plex-Token={token}'
        response = requests.get(url, headers={ 'Accept' : 'application/json' })
        json_response = {}
        try:
            json_response = json.loads(response.content)['MediaContainer']
        except:
            return
        finally:
            response.close()

        if not 'Metadata' in json_response:
            return

        refreshed = set()
        for item in json_response['Metadata']:
            metadata_id = int(item[refresh_key])
            if metadata_id in refreshed:
                continue

            for version in item['Media']:
                for part in version['Part']:
                    if part['file'].lower().startswith(self.dir.lower()):
                        refreshed.add(int(metadata_id))
                        requests.put(f'{host}/library/metadata/{metadata_id}/refresh?X-Plex-Token={token}')


if __name__ == '__main__':
    Scanner().process()
