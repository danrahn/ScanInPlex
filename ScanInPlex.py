import argparse
import json
import os
import ScanInPlexCommon as Common
from ScanInPlexConfiguration import Configure
from ScanInPlexUninstaller import Uninstall
from ScanInPlexScanner import Scanner
import subprocess
import sys
import traceback

class ScanInPlexRouter:
    def __init__(self):
        self.valid = True
        if os.name.lower() != 'nt':
            self.valid = False
            print_error(f'os "{os.name}" detected, Windows required.')
            os.system('pause')
            return
    
    def run(self):
        if not self.valid:
            return
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
            Configure(cmd_args).configure()
        elif cmd_args.scan:
            Scanner(cmd_args).scan()
        elif cmd_args.uninstall:
            Uninstall(cmd_args).uninstall()

def print_error(msg):
    print(f'ERROR: {msg}')
    print(f'Exiting...')

if __name__ == '__main__':
    ScanInPlexRouter().run()