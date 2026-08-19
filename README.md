# Fieldline — Document Intelligence UI

Django **templates + CSS + JavaScript only**. No models, APIs, or extraction pipeline.

You add the backend. This repo is the operator UI, split by app: landing, accounts, dashboard, documents, schemas, exports.

## Run

```bash
cd fieldline-document-intelligence
python manage.py runserver
```

Open http://127.0.0.1:8000/

| URL | Screen |
|-----|--------|
| `/` | Landing (demo modal) |
| `/login/` | Sign in + forgot password modal |
| `/app/` | Overview |
| `/app/inbox/` | Inbox |
| `/app/review/?doc=invoice` | Review + bounding boxes (also `receipt`, `bol`) |
| `/app/exceptions/` | Failed / rejected |
| `/app/schemas/` | Schema builder |
| `/app/exports/` | Exports + sample downloads |

Clicks open pages or modals (upload, approve, reject, export, filters, schema, alerts, account, webhook, retry, help).

## Apps

| App | What it owns |
|-----|----------------|
| `pages` | Marketing landing |
| `accounts` | Sign in |
| `dashboard` | Overview |
| `documents` | Inbox, review, exceptions |
| `schemas` | Schema builder |
| `exports` | JSON / CSV / SQL export |

Shared chrome stays in `templates/base.html` and `templates/app/base_app.html`.

## Where to plug your backend

- App `views.py` files — replace `render(...)` with queries later
- Inbox dropzone / review Approve — JS toasts; point them at your endpoints
- `documents/templates/documents/review.html` — bind field values from your extractor

## Design

Warm paper + pine sidebar. Fonts: Fraunces + Outfit.
