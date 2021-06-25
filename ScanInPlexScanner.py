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
            self.cmd_args = parser.parse_args()

        if 'directory' not in self.cmd_args:
            self.valid = False
            return

        self.dir = self.cmd_args.directory

    def scan(self):
        """
        Attempts to scan the passed in library. Fails silently
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
        dir_lower = self.dir.lower()
        for section in mappings['sections']:
            for path in [p.lower() for p in section['paths']]:

                # Passed in directory must start with one our our root folders, but not make sure to ignore
                # partial matches (e.g. Z:\Movies2\SomeFolder compared to Z:\Movies)
                if dir_lower.startswith(path) and (len(dir_lower) == len(path) or dir_lower[len(path)] == '\\'):
                    section_id = section['section']
                    break
            if section_id != -1:
                break

        if section_id == -1:
            return
        
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

if __name__ == '__main__':
    Scanner().scan()
