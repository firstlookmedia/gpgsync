import subprocess, os, platform, tempfile, shutil

class GnuPG(object):
    def __init__(self):
        self.system = platform.system()
        self.creationflags = 0
        if self.system == 'Darwin':
            self.gpg_path = '/usr/local/bin/gpg'
        elif self.system == 'Linux':
            self.gpg_path = '/usr/bin/gpg2'
        elif self.system == 'Windows':
            import win32process
            self.creationflags = win32process.CREATE_NO_WINDOW
            self.gpg_path = '{0}\GNU\GnuPG\gpg2.exe'.format(os.environ['ProgramFiles(x86)'])

        self.gpg_command = [self.gpg_path, '--batch', '--no-tty']

    def is_gpg_available(self):
        if self.system == 'Windows':
            return os.path.isfile(self.gpg_path)
        else:
            return os.path.isfile(self.gpg_path) and os.access(self.gpg_path, os.X_OK)
