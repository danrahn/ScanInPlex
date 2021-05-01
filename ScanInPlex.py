import argparse
import json
import os
import requests
import urllib
import yaml

class ScanInPlexConfiguration:
    def __init__(self):
        self.get_config()

    def get_config(self):
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

        parser = argparse.ArgumentParser()
        parser.add_argument('-h', '--host')
        parser.add_argument('-t', '--token')
        
        cmd_args = parser.parse_args()
        self.host = self.get_config_value('host', config, cmd_args, 'http://localhost:32400')
        self.token = self.get_config_value('token', config, cmd_args)


    def run(self):
        libraries = self.get_library_mappings()
        if libraries == None:
            return
        print(libraries)

    def get_config_value(self, key, config, cmd_args=None, default=''):
        if key in config and config[key] != None:
            if cmd_args != None and key in cmd_args:
                value = cmd_args.__dict__[key]
                if value != None:
                    # Command-line args shadow config file
                    print(f'WARN: Duplicate argument "{key}" found in both command-line arguments and config file. Using command-line value ("{cmd_args.__dict__[key]}")')
                    return cmd_args.__dict__[key]
            return config[key]
        if len(default) != 0:
            return default
        
        return input(f'\nCould not find "{key}" and no default is available.\n\nPlease enter a value for "{key}": ')

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


def adjacent_file(filename):
    """Returns the full path to the given file assuming it's in the same directory as the script"""

    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) + os.sep + filename

if __name__ == '__main__':
    config = ScanInPlexConfiguration()
    config.run()