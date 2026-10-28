"""Generate a private configuration without echoing credentials or overwriting."""
import argparse
import os
import secrets
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--path', default='.env')
args = parser.parse_args()
path = Path(args.path)
content = f'WE_SPEAK_SECRET_KEY={secrets.token_urlsafe(64)}\nWE_SPEAK_SITE=localhost\nWE_SPEAK_HOSTS=localhost\nWE_SPEAK_BIND=127.0.0.1\nWE_SPEAK_HTTP_PORT=8089\nWE_SPEAK_HTTPS_PORT=8449\n'
try:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(content)
except FileExistsError:
    parser.exit(1, f'Refusing to overwrite {path}\n')
print(f'Created private configuration: {path}')
