import argparse
import os
import ScanInPlexCommon as Common
import shutil
import traceback

class Uninstall:
    def __init__(self, cmd_args=None):
        self.cmd_args = cmd_args
        self.is_admin = Common.is_admin()

    def uninstall(self):
        if self.cmd_args == None:
            parser = argparse.ArgumentParser()
            parser.add_argument('-q', '--quiet', help='Don\'t prompt the user to confirm')
            self.cmd_args = parser.parse_args()

        if not self.is_admin:
            print('\n\nNOTE: Script is not running with admin privileges, which')
            print('      will result in additional prompts, even with -q\n')

        if not self.cmd_args.quiet and not Common.get_yes_no('Are you sure you want to uninstall Scan in Plex'):
            print('Uninstall cancelled. Exiting...')
            return

        errors = False
        if 'LOCALAPPDATA' in os.environ:
            config_path = os.path.join(os.environ['LOCALAPPDATA'], 'ScanInPlex')
            if os.path.exists(config_path):
                try:
                    shutil.rmtree(config_path)
                except:
                    errors = True
        if self.is_admin:
            os.system('REG DELETE HKCR\\Directory\\shell\\ScanInPlex /f >NUL')
            os.system('REG DELETE HKCR\\Directory\\shell\\RefreshInPlex /f >NUL')
        else:
            errors = errors or not self.uninstall_via_file()

        if not self.cmd_args.quiet:
            print('Uninstall complete' + (' with errors' if errors else ''))


    def uninstall_via_file(self):
        text  = f'Windows Registry Editor Version 5.00\n\n'

        text += f'[-HKEY_CLASSES_ROOT\\Directory\\shell\\ScanInPlex]\n'
        text += f'[-HKEY_CLASSES_ROOT\\Directory\\shell\\RefreshInPlex]\n'

        reg_temp = '_uninstall.tmp.reg'
        try:
            with open(reg_temp, 'w') as reg:
                reg.writelines([text])
        except Exception:
            print('\nError removing registry entries:')
            traceback.print_exc()
            return False

        os.system(f'.\\{reg_temp}')
        os.remove(reg_temp)
        return True


if __name__ == '__main__':
    Uninstall().uninstall()
