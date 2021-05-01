import argparse
import os
import ScanInPlexCommon as Common

class UninstallScanInPlex:
    def __init__(self, cmd_args=None):
        self.cmd_args = cmd_args
        self.is_admin = Common.is_admin()
    
    def run(self):
        if self.cmd_args == None:
            parser = argparse.ArgumentParser()
            parser.add_argument('-u', '--uninstall', action='store_true', help='Uninstall Scan in Plex')
            parser.add_argument('-q', '--quiet', help='Don\'t prompt the user to confirm')
            self.cmd_args = parser.parse_args()
        
        if not self.is_admin:
            print('\n\nNOTE: Script is not running with admin privileges, which')
            print('      will result in additional prompts, even with -q\n')

        if not self.cmd_args.quiet and not Common.get_yes_no('Are you sure you want to uninstall Scan in Plex'):
            print('Uninstall cancelled. Exiting...')
            return

        self.uninstall()

    def uninstall(self):
        if self.is_admin:
            os.system('REG DELETE HKCR\\Directory\\shell\\ScanInPlex /f >NUL')
        else:
            self.uninstall_via_file()
    
    def uninstall_via_file(self):
        text  = f'Windows Registry Editor Version 5.00\n\n'

        text += f'[-HKEY_CLASSES_ROOT\\Directory\\shell\\ScanInPlex]\n'

        reg_temp = '_uninstall.tmp.reg'
        try:
            with open(reg_temp, 'w') as reg:
                reg.writelines([text])
        except Exception as e:
            print('\nError removing registry entries:')
            raise e
        
        os.system(f'.\\{reg_temp}')
        os.remove(reg_temp)
        return

if __name__ == '__main__':
    UninstallScanInPlex().run()
