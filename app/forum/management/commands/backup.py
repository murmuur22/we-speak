"""Create a consistent, private SQLite snapshot, including image blobs."""
import os
import sqlite3
import time
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Back up all forum data to a NEW private SQLite file; never overwrites.'

    def add_arguments(self, parser):
        parser.add_argument('destination')

    def handle(self, *args, **options):
        path = Path(options['destination']).expanduser().absolute()
        created = False
        try:
            if connection.vendor != 'sqlite':
                raise CommandError('This command supports SQLite only.')
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            created = True
            deadline = time.monotonic() + 60

            def progress(status, remaining, total):
                if time.monotonic() > deadline:
                    raise TimeoutError('Backup exceeded 60 seconds; try again during a quieter period.')

            connection.ensure_connection()
            with sqlite3.connect(path) as destination:
                connection.connection.backup(destination, pages=256, progress=progress, sleep=0.05)
                if destination.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                    raise CommandError('Backup integrity check failed.')
            self.stdout.write(f'Backup verified: {path}')
        except (OSError, sqlite3.Error, TimeoutError, CommandError) as exc:
            if created:
                path.unlink(missing_ok=True)
            raise CommandError(str(exc)) from exc
