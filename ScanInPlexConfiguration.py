import argparse
import json
import os
import requests
import shutil
import urllib
import yaml

class ScanInPlexConfiguration:
    def __init__(self, cmd_args):
        self.get_config(cmd_args)

    def get_config(self, cmd_args):
        """Reads the config file from disk, asking the user for input for any missing items"""

        config_file = adjacent_file('config.yml')
        config = None
        if not os.path.exists(config_file):
            print('WARN: Could not fine config.yml in the same directory as this script. Falling back to commandline/user input')
        else:
            with open(config_file, encoding='utf-8') as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)

        if not config:
            config = {}

        self.host = self.get_config_value('host', config, cmd_args, 'http://localhost:32400')
        self.token = self.get_config_value('token', config, cmd_args)
        self.pms_path = None
        self.pyw_path = None


    def run(self):
        sections = self.get_library_mappings()
        if sections == None:
            return

        if len(sections) == 0:
            print('Couldn\'t find any sections. Have you added libraries to Plex?')
            return None
        
        print('\nFound library mappings:\n')
        for section in sections:
            print(f'\tSection {section["section"]}:')
            for section_path in section['paths']:
                print(f'\t\t{section_path}')
            print()
        
        if not self.get_yes_no('Do you want to use the following mappings'):
            print('Exiting...')
            return

        self.create_registry_entries(sections)
        self.create_mapping_json(sections)


    def get_library_mappings(self):
        sections = self.get_json_response('/library/sections', { 'X-Plex-Features' : 'external-media,indirect-media' })
        if sections == None:
            print('Sorry, something went wrong processing library sections. Make sure your host and token are properly set')
            return None

        mappings = []

        if 'Directory' not in sections:
            print('Malformed response from host, exiting...')
            return None

        for section in sections['Directory']:
            mappings.append({ 'section' : section['key'], 'paths' : [entry['path'] for entry in section['Location']] })
        return mappings


    def create_registry_entries(self, sections):
        """
        Adds the right registry entries to enable the context menu entries
        
        It currently does this by create a temporary .reg file and executing it.
        It might be cleaner to invoke REG ADD commands via os.system, but this works too
        """

        text  = 'Windows Registry Editor Version 5.00\n\n'

        text += '[HKEY_CLASSES_ROOT\\Directory\\shell\\ScanInPlex]\n'
        text += '@="Scan in Plex"\n'
        text += '"Icon"="\\"' + self.get_pms_path().replace('\\', '\\\\') + '\\",0"\n'
        text += '"AppliesTo"="' + self.get_appliesTo_path(sections) + '"\n' # backslashes must be escaped
        text += '"MultiSelectModel"="Document"\n\n'

        text += '[HKEY_CLASSES_ROOT\\Directory\\shell\\ScanInPlex\\command]\n'
        text += '@="\\"' + self.get_pythonw_path().replace('\\', '\\\\') + '\\" \\"' + adjacent_file('ScanInPlex.py').replace('\\', '\\\\') + '\\" -s -d \\"%1\\""\n'

        print('Adding registry entries. This may launch a UAC dialog...', end='', flush=True)
        reg_temp = '_scanInPlex.tmp.reg'
        try:
            with open(reg_temp, 'w') as reg:
                reg.writelines([text])
        except Exception as e:
            print('Error adding registry entries:')
            raise e
        
        os.system(f'.\\{reg_temp}')
        os.remove(reg_temp)
        print(' Done!')


    def create_mapping_json(self, sections):
        config = {
            'exe' : self.get_scanner_path(),
            'sections' : sections
        }
        
        print('Writing config file...')
        with open('config.json', 'w') as f:
            json.dump(config, f)


    def get_pms_path(self):
        """
        Attempts to find the path to Plex Media Server.exe to use its icon in the context menu

        If not found, prompt the user to enter the full path the the executable
        """

        if self.pms_path != None:
            return self.pms_path
        for program_files in ['PROGRAMFILES(X86)', 'PROGRAMFILES']:
            if program_files in os.environ:
                self.pms_path = os.path.join(os.environ[program_files], 'Plex', 'Plex Media Server', 'Plex Media Server.exe')
                if os.path.exists(self.pms_path):
                    return self.pms_path

        self.pms_path = input('Could not find "Plex Media Server.exe", please enter the full path: ')
        while not os.path.exists(self.pms_path):
            self.pms_path = input("That path doesn't exist, please enter the complete path to Plex Media Server.exe (e.g. 'C:\\Program Files\\Plex\\Plex Media Server\\Plex Media Server.exe') ")
        return self.pms_path


    def get_appliesTo_path(self, sections):
        """
        Return the AppliesTo registry value based on the given sections
        """

        applies_to = ''
        for section in sections:
            for path in section['paths']:
                applies_to += ' OR System.ItemPathDisplay:~=\\"' + path.replace('\\', '\\\\') + '\\"'
        return applies_to[4:]


    def get_pythonw_path(self):
        """
        Returns the path to pythonw, which we'll use to silently launch our script
        """

        if self.pyw_path:
            return self.pyw_path

        self.pyw_path = shutil.which('pythonw')
        if self.pyw_path == None:
            self.pyw_path = input('Could not find pythonw in your PATH. Please enter the full path to pythonw.exe\n> ')
        while not os.path.exists(self.pyw_path):
            self.pyw_path = input('Could not find that file. Please enter the full path to pythonw.exe: ')
        return self.pyw_path


    def get_scanner_path(self):
        if self.pms_path != None:
            scanner = os.path.join(self.pms_path[:self.pms_path.rfind(os.sep)], 'Plex Media Scanner.exe')
            if os.path.exists(scanner):
                return scanner
        
        scanner = input('Could not find Plex Media Scanner.exe, please enter the full path: ')
        while not os.path.exists(scanner):
            scanner = input('That path does not exists, please enter the complete path to Plex Media Scanner.exe: ')
        return scanner


    def get_config_value(self, key, config, cmd_args=None, default=''):
        cmd_arg = None
        if cmd_args != None and key in cmd_args:
            cmd_arg = cmd_args.__dict__[key]
        
        if key in config and config[key] != None:
            if cmd_arg != None:
                # Command-line args shadow config file
                print(f'WARN: Duplicate argument "{key}" found in both command-line arguments and config file. Using command-line value ("{cmd_args.__dict__[key]}")')
                return cmd_arg
            return config[key]
        
        if cmd_arg != None:
            return cmd_arg

        if len(default) != 0:
            return default
        
        return input(f'\nCould not find "{key}" and no default is available.\n\nPlease enter a value for "{key}": ')


    def get_json_response(self, url, params={}):
        response = requests.get(self.url(url, params), headers={ 'Accept' : 'application/json' })
        try:
            data = json.loads(response.content)['MediaContainer']
        except:
            print('Error: Unexpected JSON response:\n')
            print(response.content)
            print()
            data = None
        response.close()
        return data


    def url(self, base, params={}):
        real_url = f'{self.host}{base}'
        sep = '?'
        for key, value in params.items():
            real_url += f'{sep}{key}={urllib.parse.quote(value)}'
            sep = '&'
        
        return f'{real_url}{sep}X-Plex-Token={self.token}'


    def get_yes_no(self, prompt):
        while True:
            response = input(f'{prompt} (y/n)? ')
            ch = response.lower()[0] if len(response) > 0 else 'x'
            if ch in ['y', 'n']:
                return ch == 'y'


def adjacent_file(filename):
    """Returns the full path to the given file assuming it's in the same directory as the script"""

    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) + os.sep + filename