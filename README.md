# WE Speak

A small self-hosted forum: one board, a quiet interface, and ownership of your own words. **Development preview — not a stable release or a completed security audit.**

- Username/password accounts, private own-post/comment history, and login-bound identity.
- Accounts start discussions; guests can comment and react.
- Authors edit/delete their own posts and comments. Deleting a parent preserves other people's comments.
- Emoji reactions and bounded PNG/JPEG/WebP image attachments.
- Separate staff-only health/storage view, identity disable/restore and operator action history.
- Django, SQLite and server-rendered HTML. Runs independently of Relay.

## Local development

Python 3.11+ and uv:

```sh
git clone https://github.com/murmuur22/we-speak.git
cd we-speak
uv venv --python 3.11 app/.venv
uv pip install --python app/.venv/bin/python -r app/requirements.txt
WE_SPEAK_DEV=1 app/.venv/bin/python app/manage.py migrate
WE_SPEAK_DEV=1 app/.venv/bin/python app/manage.py collectstatic --noinput
WE_SPEAK_DEV=1 app/.venv/bin/python app/manage.py runserver 127.0.0.1:8000 --noreload
```

Development mode is explicit and uses an ephemeral secret unless supplied; restarting can invalidate sessions. Normal installations start empty. Do not use Django's development server for internet hosting.

```sh
WE_SPEAK_DEV=1 app/.venv/bin/python app/manage.py test forum
```

The explicit `forum` test label matters when running from the repository root. An unlabelled discovery command from that directory can select zero tests.

## Docker and HTTPS

Docker Compose runs a nonroot Gunicorn app with WhiteNoise static serving, a private SQLite volume, and a Caddy HTTPS proxy. No host database or container registry is required. Base images and Python dependencies are pinned; periodically review/update those pins and advisories.

```sh
python3 tools/init_env.py
docker compose up -d --build --wait
docker compose exec app python manage.py createsuperuser
```

The helper creates a new private `.env`, refuses overwrites and never prints its secret. Keep it out of Git. Default addresses are **loopback-only**: HTTPS at `https://localhost:8449`, HTTP at `http://localhost:8089`. Caddy's localhost certificate uses its own local CA. Do not disable browser certificate verification or change your OS trust automatically; either explicitly trust that local CA for your own test machine or use a real domain with normally trusted HTTPS.

For a real hostname, edit the private `.env`: set `WE_SPEAK_SITE=forum.example.org`, `WE_SPEAK_HOSTS=localhost,forum.example.org`, and deliberately choose bind address/ports. A public installation normally uses ports 80/443 and requires DNS, firewall and game-independent network access decisions made by the operator. No DNS, firewall or Relay configuration is automated here. This source publication does not deploy a service.

The app has no published port in Compose and trusts forwarded HTTPS only from this operator-controlled proxy topology. Caddy replaces `X-Forwarded-Proto`. Never enable `WE_SPEAK_TRUST_PROXY=1` on an app directly reachable by untrusted clients. Without explicit hosts, standalone settings retain safe loopback host defaults; they do not accept arbitrary hosts. HTTPS redirect/secure cookies are enforced outside development; `/healthz/` is a minimal database-connectivity probe exempted from HTTPS redirect for internal healthchecks. Iframes are denied; Relay integration is not implemented.

Leave your forum session before signing into an operator identity. Maintenance is `/maintenance/`; `/admin/` remains Django's permission-controlled account tools. The web dashboard cannot disable operator accounts. Use local admin tools for those deliberate changes.

## Backups and updates

A backup includes accounts, password hashes, posts, comments, reactions, operator history and image bytes. Treat it as sensitive data. The command makes a consistent SQLite backup, verifies integrity, sets mode 0600 and refuses an existing destination. Store the destination in an operator-controlled private directory.

```sh
docker compose exec app python manage.py backup /data/snapshot-before-update.sqlite3
docker compose cp app:/data/snapshot-before-update.sqlite3 ./snapshot-before-update.sqlite3
```

Move the exported snapshot to private off-host storage; snapshots left inside the live volume are not disaster recovery. No scheduled backup is enabled. Keep the deployment secret separately. Never commit snapshots or `.env`.

Before updating: snapshot/export, record your current Git commit, read CHANGELOG, pull the intended source, then `docker compose up -d --build --wait`. SQLite schema migrations run before Gunicorn starts. This is not a promise that arbitrary future migrations are downgrade-compatible.

For rollback, stop the app, retain its current volume/snapshot, and restore a known-good snapshot into a **fresh private data volume/directory** with the matching earlier source version. Preserve UID 10001 ownership for containers. Check integrity, start only that restored instance, verify login, posts and image access, then switch traffic. Do not overwrite a live database or use `docker compose down -v` as an update command. `docker compose down` preserves named volumes.

## Boundaries

Guest ownership lasts only while the browser retains its session. Guests are not unique people or guaranteed anonymous to the operator. Losing a password currently requires operator-assisted recovery through local tools; there is no email reset flow.

Images are decoded/re-encoded to fresh PNG pixels, stripping metadata and trailing bytes. Three per post/comment, 5 MiB per source/normalized image, 16 million pixels, 512 MiB total logical image storage. SQLite blobs keep the small deployment transactional; this is not a media-library design. PDF, arbitrary downloads, SVG, animation, video and custom emoji are unsupported. Deletion removes live content/own images but cannot erase other people's quotations, copies or old backups; SQLite deletion is not forensic secure erasure.

Fixed-window limits: login 12/minute, registrations 5/hour, other writes 60/minute per observed source IP. Proxy users currently share the proxy's quota; forwarded client IP headers are not trusted. These are basic limits, not comprehensive spam/DDoS protection. The proxy also caps request bodies. Temporary source uploads are private files under the data directory and are normally removed after requests; inspect crash remnants only while service processes are stopped. Back up the database, not transient upload files.

Still pending: wider device/accessibility and sustained-load qualification, recovery UX, broader attachment types, optional manual moderation controls, full dependency/license audit and a stable release. See CHANGELOG for verified milestones.

## License

WE Speak is licensed under the [MIT License](LICENSE). Copyright (c) 2026 murmuur22 and contributors. Third-party dependencies retain their own licenses. This license does not change the project's development-preview status or imply a security warranty.
