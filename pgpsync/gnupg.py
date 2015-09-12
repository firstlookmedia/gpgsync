import subprocess, os, platform, tempfile, shutil
import common

class InvalidFingerprint(Exception):
    pass

class InvalidKeyserver(Exception):
    pass

class NotFoundOnKeyserver(Exception):
    pass

class NotFoundInKeyring(Exception):
    pass

class RevokedKey(Exception):
    pass

class ExpiredKey(Exception):
    pass

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

    def is_gpg_available(self):
        if self.system == 'Windows':
            return os.path.isfile(self.gpg_path)
        else:
            return os.path.isfile(self.gpg_path) and os.access(self.gpg_path, os.X_OK)

    def recv_key(self, keyserver, fp):
        if not common.valid_fp(fp):
            raise InvalidFingerprint(fp)

        fp = common.clean_fp(fp)
        keyserver = common.clean_keyserver(keyserver)

        out,err = self._gpg(['--keyserver', keyserver, '--recv-keys', fp])

        if "No keyserver available" in err:
            raise InvalidKeyserver(keyserver)

        if "not found on keyserver" in err or "keyserver receive failed: No data" in err:
            raise NotFoundOnKeyserver(fp)

    def test_key(self, fp):
        fp = common.clean_fp(fp)
        out,err = self._gpg(['--with-colons', '--list-keys', fp])

        if "error reading key: No public key" in err:
            raise NotFoundInKeyring(fp)

        for line in out:
            if line.startswith('pub:'):
                chunks = line.split(':')
                if chunks[1] == 'r':
                    raise RevokedKey(fp)
                if chunks[1] == 'e':
                    raise ExpiredKey(fp)

    def _gpg(self, args, input=None):
        p = subprocess.Popen([self.gpg_path, '--batch', '--no-tty'] + args,
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        if input:
            (out, err) = p.communicate(input)
        else:
            p.wait()
            out = p.stdout.read()
            err = p.stderr.read()

        if out != '':
            print 'stdout', out
        if err != '':
            print 'stderr', err
        return out, err
