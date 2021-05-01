import argparse
import json
import os
import requests
import ScanInPlexCommon as Common
import shutil
import urllib
import yaml

class Configure:
    def __init__(self, cmd_args):
        self.get_config(cmd_args)

    def get_config(self, cmd_args):
        """Reads the config file from disk, asking the user for input for any missing items"""

        config_file = Common.adjacent_file('config.yml')
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
        self.verbose = cmd_args != None and cmd_args.verbose
        self.quiet = cmd_args != None and cmd_args.quiet
        if self.verbose and self.quiet:
            print('WARN: Both --verbose and --quiet specified. Keeping --verbose')
            self.quiet = False
        self.pms_path = None
        self.pyw_path = None

        self.is_admin = Common.is_admin()

        if not self.quiet:
            print('\n\nWelcome to the Scan in Plex configuration.\n')
            print('This will scan your Plex library for all folders that hold your media and add')
            print('context menu entries in Windows Explorer that lets you quickly run partial scans')
            print('on your media.\n')
            if self.is_admin:
                os.system('pause')

        if not self.is_admin and not self.quiet:
            print('\nNOTE: Script is not running with admin privileges. This script modifies the')
            print('      registry, which requires elevation. You may see a UAC prompt, as well')
            print('      as a warning about modifying the registry. This is expected.\n')
            os.system('pause')


    def configure(self):
        sections = self.get_library_mappings()
        if sections == None:
            return

        if len(sections) == 0:
            print('Couldn\'t find any sections. Have you added libraries to Plex?')
            return None
        
        if self.verbose:
            print('\nFound library mappings:\n')
            for section in sections:
                print(f'  Section {section["section"]}:')
                for section_path in section['paths']:
                    print(f'    {section_path}')
                print()

            if not Common.get_yes_no('Do you want to use these mappings'):
                print('Exiting...')
                return

        if self.create_registry_entries(sections):
            self.create_mapping_json(sections)
            if not self.quiet:
                print('\nContext menu entries have been added!')


    def get_library_mappings(self):
        if not self.quiet:
            print('Looking for library sections...', end='', flush=True)
        sections = self.get_json_response('/library/sections', { 'X-Plex-Features' : 'external-media,indirect-media' })
        if not self.quiet:
            print('Done')
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
        """

        base_key = 'HKEY_CLASSES_ROOT\\Directory\\shell\\ScanInPlex'
        icon_path = self.get_pms_path()
        applies_to = self.get_appliesTo_path(sections)
        pythonw_path = self.get_pythonw_path()
        scanner = Common.adjacent_file('Scanner.py')
        
        if self.is_admin:
            return self.create_registry_entries_as_admin(base_key, icon_path, applies_to, pythonw_path, scanner)
        else:
            return self.create_registry_entries_from_file(base_key, icon_path, applies_to, pythonw_path, scanner)

    def create_registry_entries_as_admin(self, base_key, icon_path, applies_to, pythonw_path, scanner):
        """
        Uses REG ADD to add the right registry keys. Avoids the UAC and registry prompts,
        but can only be run as an administrator
        """
        commands = [
            f'REG ADD {base_key} /ve /t REG_SZ /d "Scan In Plex"',
            f'REG ADD {base_key} /v "Icon" /t REG_SZ /d "\\"{icon_path}\\",0"',
            f'REG ADD {base_key} /v "AppliesTo" /t  REG_SZ /d "{applies_to}"',
            f'REG ADD {base_key} /v "MultiSelectModel" /t REG_SZ /d "Document"',
            f'REG ADD {base_key}\\command /ve /t REG_SZ /d "\\"{pythonw_path}\\" \\"{scanner}\\" -d \\"%1\\""'
        ]

        if self.verbose:
            print('\n\nRegistry modifications:\n')
            for cmd in commands:
                print(cmd)
            print()
            if not Common.get_yes_no('Do you want to make the above registry changes'):
                print ('Exiting...')
                return False

        if not self.quiet:
            print('Adding registry entries...', end='', flush=True)
        for cmd in commands:
            os.system(f'{cmd} /f >NUL')
        if not self.quiet:
            print('Done!')
        return True


    def create_registry_entries_from_file(self, base_key, icon_path, applies_to, pythonw_path, scanner):
        """
        Adds registry entries by creating a .reg file and executing it. Used as
        a backup for when the script is not run with administrator privileges
        """

        # .reg files need extra escapes
        icon_path = icon_path.replace('\\', '\\\\')
        pythonw_path = pythonw_path.replace('\\', '\\\\')
        scanner = scanner.replace('\\', '\\\\')

        text  = f'Windows Registry Editor Version 5.00\n\n'

        text += f'[{base_key}]\n'
        text += f'@="Scan in Plex"\n'
        text += f'"Icon"="\\"{icon_path}\\",0"\n'
        text += f'"AppliesTo"="{applies_to}"\n'
        text += f'"MultiSelectModel"="Document"\n\n'

        text += f'[{base_key}\\command]\n'
        text += f'@="\\"{pythonw_path}\\" \\"{scanner}\\" -d \\"%1\\""\n'

        if self.verbose:
            print('\n\nRegistry modifications:\n')
            print(f'{text}')
            if not Common.get_yes_no('Do you want to make the above registry changes'):
                print('Exiting...')
                return False

        if not self.quiet:
            print('Adding registry entries. This may launch a UAC dialog...', end='', flush=True)
        reg_temp = '_scanInPlex.tmp.reg'
        try:
            with open(reg_temp, 'w') as reg:
                reg.writelines([text])
        except Exception as e:
            print('\nError adding registry entries:')
            raise e
        
        os.system(f'.\\{reg_temp}')
        os.remove(reg_temp)
        if not self.quiet:
            print(' Done!')
        return True


    def create_mapping_json(self, sections):
        config = {
            'exe' : self.get_scanner_path(),
            'sections' : sections
        }

        if not self.quiet:
            print('Writing config file...', end='', flush=True)
        with open('config.json', 'w') as f:
            json.dump(config, f)
        if not self.quiet:
            print('Done!')


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
                # extra backslashes are needed if we're creating a .reg file
                final_path = path
                if not self.is_admin:
                    final_path = final_path.replace('\\', '\\\\')
                applies_to += ' OR System.ItemPathDisplay:~=\\"' + final_path + '\\"'
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
