# Scan in Plex

The Scan in Plex script adds a 'Scan in Plex' context menu entry in Windows Explorer for folders that are part of your Plex library.

## Usage

`python ScanInPlex.py -h | -c [-p HOST] [-t TOKEN] | -s -d DIRECTORY`

To set up ScanInPlex, run `python ScanInPlex.py -c` (see [Configuration](#Configuration) below)

## Requirements

Requirements are outlined in requirements.txt, and can be installed via `pip install -r requirements.txt`

## Configuration

Only two arguments are required, `host` and `token`. They can be specified in the provided `config.yml` file, or passed in as command line arguments:

Value | Command line | Description
---|---|---
host | `--host` | The host of the Plex server. Defaults to http://localhost:32400
token | `-t`, `--token` | Your Plex token. Se Plex's official documentation for [Finding an authentication token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)

## Implementation Details

This script has three main parts:
1. Query your Plex server to grab all your library sections and the folders mapped to those sections
2. Create the necessary registry entries to [create the shortcut menu handlers](https://docs.microsoft.com/en-us/windows/win32/shell/context-menu-handlers).
3. Create a configuration file that ScanInPlex will reference to properly invoke `Plex Media Scanner.exe`