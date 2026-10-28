"""Run migrations once, then replace this process with the WSGI server."""
import os
import subprocess
import sys

os.umask(0o077)
subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True)
os.execvp('gunicorn', ['gunicorn', 'config.wsgi:application', '--bind', '0.0.0.0:8000',
                      '--workers', '1', '--threads', '4', '--timeout', '45',
                      '--access-logfile', '-', '--error-logfile', '-'])
