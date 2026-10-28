# Application source

The Django application lives here; [the repository README](../README.md) is the canonical setup, self-hosting, security-boundary and backup guide. [CHANGELOG](../CHANGELOG.md) records implementation and verification milestones.

For a development shell already in this directory:

```sh
WE_SPEAK_DEV=1 .venv/bin/python manage.py migrate
WE_SPEAK_DEV=1 .venv/bin/python manage.py collectstatic --noinput
WE_SPEAK_DEV=1 .venv/bin/python manage.py test forum
WE_SPEAK_DEV=1 .venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Do not expose the development server publicly. Source is a development preview; license selection and stable-release qualification are pending.
