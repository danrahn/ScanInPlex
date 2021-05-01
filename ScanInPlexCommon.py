import ctypes
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_yes_no(prompt):
    while True:
        response = input(f'{prompt} (y/n)? ')
        ch = response.lower()[0] if len(response) > 0 else 'x'
        if ch in ['y', 'n']:
            return ch == 'y'


def adjacent_file(filename):
    """Returns the full path to the given file assuming it's in the same directory as the script"""

    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) + os.sep + filename
