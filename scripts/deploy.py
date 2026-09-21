"""Upload only three public files to an existing, explicitly selected FTPS directory."""
import ftplib
import os
import ssl
from pathlib import Path

def deploy():
    host, user, password, directory = [os.environ[k] for k in ('W4Y_FTP_HOST', 'W4Y_FTP_USER', 'W4Y_FTP_PASSWORD', 'W4Y_FTP_DIR')]
    if any('\n' in x or '\r' in x for x in (host, user, directory)):
        raise ValueError('Invalid connection settings')
    if not directory.strip(): raise ValueError('Set an explicit target directory')
    # Explicit TLS on port 21. No cleartext fallback; verify the server certificate.
    with ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=45) as ftp:
        ftp.connect(host, 21)
        ftp.login(user, password)
        ftp.prot_p()
        ftp.set_pasv(True)
        ftp.cwd(directory)  # Never create or guess a web root.
        root = Path(__file__).resolve().parents[1] / 'site'
        for name in ('status.json', 'index.html', 'favicon.svg'):
            with (root / name).open('rb') as src:
                ftp.storbinary('STOR ' + name + '.upload', src)
            ftp.rename(name + '.upload', name)
    print('Published the three page files.')

if __name__ == '__main__': deploy()
