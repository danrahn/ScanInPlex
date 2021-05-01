import argparse
import json
import os
import ScanInPlexCommon as Common
import subprocess

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
            config_string = ''.join(f.readlines()).lower()

        mappings = json.loads(config_string)
        section = -1
        dir_lower = self.dir.lower()
        for section in mappings['sections']:
            for path in section['paths']:
                if dir_lower.startswith(path):
                    section = section['section']
                    break
            if section != -1:
                break

        if section == -1:
            return

        exe = mappings['exe']
        cmd = f'"{exe}" -s -c {section} -d "{self.dir}"'
        CREATE_NO_WINDOW = 0x08000000 # Don't show any output
        subprocess.call(cmd, creationflags=CREATE_NO_WINDOW)

if __name__ == '__main__':
    Scanner().scan()
