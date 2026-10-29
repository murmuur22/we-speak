# Changelog

## Unreleased — hardening and self-hosting preview
- Connect the project to `https://github.com/murmuur22/we-speak.git`; keep local prototypes, databases, secrets and workstation-only evidence out of source control. This is a development preview, not a stable release.
- Add the owner-approved MIT License, credited to murmuur22 and contributors, and update documentation. Third-party dependencies retain their own licenses.
- Redact authentication password fields from diagnostic reports, prevent caching of dynamic/private pages and use a private transient-upload directory.
- Implement staff-only database/storage status, paginated identities, audited disable/restore with conversations preserved, and protection against disabling operator accounts through the web dashboard.
- Add an integrity-checked, private, overwrite-refusing SQLite backup command, including image bytes; exercise snapshot restoration and password/image recovery on isolated synthetic data.
- Add nonroot Gunicorn/WhiteNoise Docker packaging, Caddy HTTPS, a private app network, explicit proxy trust, loopback-only default exposure, private configuration generation and Python 3.11/3.12 CI.
- Fix build-time upload-spool ownership caught in review: preserve mode 0700 with runtime UID/GID 10001. Reproduce the baseline failure in the real container, then verify a fresh image/volume with a valid disk-spooled PNG upload, download and empty transient directory.
- Update Pillow to 13.0.0 after the dependency audit; repeat pip-audit reports no known vulnerabilities in the pinned Python requirements. This does not qualify OS images or all third-party licenses.
- Correct the initial hosted-CI configuration to use a job-level supported data-directory value; retain explicit nonzero test discovery.
- Verification: 42 application tests pass locally and in the rebuilt container; trusted-CA HTTPS, secure cookies, static assets, maintenance authorization/CSRF, and image-inclusive backup/restore exercised. Public-domain deployment, broad device/load coverage and stable-release qualification remain separate gates.

## Earlier — first working development build
- Implement standalone Django/SQLite app in `app/`, retaining both earlier visual prototypes. Real username/password accounts, own history, account-only discussion creation, guest comments, author edit/delete, deleted-parent placeholders preserving others' comments, and standard emoji toggles.
- Add bounded normalized raster-image attachments to posts/comments; images stored transactionally in SQLite. Nonimage/video uploads deferred. Add CSRF, server-side ownership, persistent write limits and explicit nonproduction/deployment boundaries.
- Parent verification: 33 initial application tests, 29 real browser checks, desktop/mobile screenshots, isolated SQLite backup/restore plus restored HTTP account/history/comment checks passed. Initial reviewer independently ran 33 tests and bounded adversarial/concurrency checks.
- Independent review found admin login could replace an active forum identity with valid staff credentials without leaving. Reproduced with three failing identity controls and a passing explicit-leave control, then guarded the operator entry point. All 37 application tests now pass. Independent repair recheck accepted the identity guard after nine targeted tests, clearing the local-development blocker; release readiness remains false.
- Retain nonblocking production review items: password-field diagnostic redaction, private-page cache/temp-file handling and production host-setting documentation consistency. Maintenance dashboard, production packaging, dependency audit, accessibility/device coverage, license and public release remain unfinished. No publication/deployment or other-project changes.
- Parent-owned local browser/restore servers stopped; no listener remains on their test port.

## Earlier — UI prototype 02
- Current revision: `prototype-v2/index.html`; prototype 01 preserved unchanged in `prototype/`.
- Applied Robbie's blank-canvas direction: removed slogans, colored banners, entry preview feed, row numbers, badges, excerpts and repeated explanations. Neutral canvas, compact branding, essential controls and thin discussion separators.
- Preserved login-bound identity, anonymous entry, posting/replies and local-only maintenance preview. No backend, production or Relay changes.
- Browser suite: 33 checks passed, no page errors; actual desktop/mobile screenshots rerendered. Desktop board and mobile entry visually inspected.

## Earlier — UI prototype 01
- Implement self-contained local entry/sign-in/create-demo-identity/anonymous flows with session-bound authorship and no per-post identity picker.
- Add single-board list, search/sort, discussion/reply views, quote references and new-discussion form, with local demo persistence and literal escaped user text.
- Add separately labeled maintenance preview with unconnected health/backup/log states, sample identity controls and reversible sample-post hiding. No real admin authentication or service operations.
- Establish original stark/friendly pink-black-paper interface, mobile layouts, visible keyboard focus and primary touch controls.
- Capture desktop/mobile screenshots and exercise complete prototype in headless Chromium. Production backend/auth/Relay/deployment remain unimplemented.
