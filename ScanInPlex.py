import argparse
import json
import os
from ScanInPlexConfiguration import ScanInPlexConfiguration
import subprocess
import sys
import traceback


class ScanInPlex:
    def __init__(self, cmd_args):
        self.valid = True
        print(cmd_args)
        if 'directory' not in cmd_args:
            self.valid = False
            print_error('Directory not specified for scan')
        
        self.dir = cmd_args.directory
    
    def scan(self):
        config_file = os.path.join(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))), 'config.json')
        if not os.path.exists(config_file):
            sys.exit(0)

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
            sys.exit(0)

        exe = mappings['exe']
        cmd = f'"{exe}" -s -c {section} -d "{self.dir}"'
        CREATE_NO_WINDOW = 0x08000000 # Don't show any output
        subprocess.call(cmd, creationflags=CREATE_NO_WINDOW)

class ScanInPlexRouter:
    def __init__(self):
        self.valid = True
        if os.name.lower() == 'windows':
            self.valid = False
            print_error(f'os "{os.name}" detected, Windows required.')
            os.system('pause')
            return
    
    def run(self):
        parser = argparse.ArgumentParser(usage='ScanInPlex.py [-h] [-c [-p HOST] [-t TOKEN]] | [-s -d DIR]')
        parser.add_argument('-c', '--configure', action="store_true", help="Configure ScanInPlex")
        parser.add_argument('-p', '--host', help='Plex host (e.g. http://localhost:32400)')
        parser.add_argument('-t', '--token', help='Plex token')

        parser.add_argument('-s', '--scan', help='Scan a folder in Plex', action="store_true")
        parser.add_argument('-d', '--directory', help='Folder to scan')

        cmd_args = parser.parse_args()
        if cmd_args.configure and cmd_args.scan:
            print_error('Cannot specify both configure and scan')
            return
        if cmd_args.configure:
            config = ScanInPlexConfiguration(cmd_args)
            config.run()
        elif cmd_args.scan:
            scanner = ScanInPlex(cmd_args)
            if scanner.valid:
                scanner.scan()

def print_error(msg):
    print(f'ERROR: {msg}')
    print(f'Exiting...')

if __name__ == '__main__':
    print('starting...')
    router = ScanInPlexRouter()
    if router.valid:
        router.run()