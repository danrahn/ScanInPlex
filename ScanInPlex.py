import argparse
import json
import os
import ScanInPlexCommon as Common
from ScanInPlexConfiguration import ScanInPlexConfiguration
import UninstallScanInPlex as Uninstall
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
        config_file = Common.adjacent_file('config.json')
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
        if os.name.lower() != 'nt':
            self.valid = False
            print_error(f'os "{os.name}" detected, Windows required.')
            os.system('pause')
            return
    
    def run(self):
        parser = argparse.ArgumentParser(usage='ScanInPlex.py [-h] [-c [-p HOST] [-t TOKEN] [-v | -q]] | [-s -d DIR] | -u [-q]')
        parser.add_argument('-c', '--configure', action="store_true", help="Configure ScanInPlex")
        parser.add_argument('-p', '--host', help='Plex host (e.g. http://localhost:32400)')
        parser.add_argument('-t', '--token', help='Plex token')
        parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output')
        parser.add_argument('-q', '--quiet', action='store_true', help='Only show error messages')

        parser.add_argument('-s', '--scan', help='Scan a folder in Plex', action="store_true")
        parser.add_argument('-d', '--directory', help='Folder to scan')

        parser.add_argument('-u', '--uninstall', action="store_true", help='Uninstall Scan in Plex (delete regkeys)')

        cmd_args = parser.parse_args()
        count = sum([1 if arg else 0 for arg in [cmd_args.configure, cmd_args.scan, cmd_args.uninstall]])
        if count > 1:
            print_error('Cannot specify multiple top-level commands (configure, scan, uninstall)')
            return
        if cmd_args.configure:
            config = ScanInPlexConfiguration(cmd_args)
            config.run()
        elif cmd_args.scan:
            scanner = ScanInPlex(cmd_args)
            if scanner.valid:
                scanner.scan()
        elif cmd_args.uninstall:
            Uninstall.UninstallScanInPlex(cmd_args).run()

def print_error(msg):
    print(f'ERROR: {msg}')
    print(f'Exiting...')

if __name__ == '__main__':
    router = ScanInPlexRouter()
    if router.valid:
        router.run()