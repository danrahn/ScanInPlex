# Scan in Plex

The Scan in Plex script adds a 'Scan in Plex' context menu entry in Windows Explorer for folders that are part of your Plex library.

## Usage

`python ScanInPlex.py [args]`

## Requirements

Requirements are outlined in requirements.txt, and can be installed via `pip install -r requirements.txt`

## Configuration

Only two arguments are required, `host` and `token`. They can be specified in the provided `config.yml` file, or passed in as command line arguments:

Value | Command line | Description
---|---|---
host | `--host` | The host of the Plex server. Defaults to http://localhost:32400
token | `-t`, `--token` | Your Plex token. Se Plex's official documentation for [Finding an authentication token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
