# Booklat Demo Mode

This app seeds a complete, realistic library for public demos. Everything is
driven from the JSON files in [`data/`](data/), so the dataset can be edited
without touching the views.

## Enable demo mode

Set these values in `.env`:

```env
DEMO_MODE=1
DEMO_PASSWORD=Booklat@Demo2026!
```

Then start the app normally:

```bash
docker compose up
```

The Docker entrypoint runs `seed_data` and, when `DEMO_MODE=1`, `seed_demo`.
For a local run:

```bash
DEMO_MODE=1 python manage.py seed_data
DEMO_MODE=1 python manage.py seed_demo
DEMO_MODE=1 python manage.py runserver
```

## Demo accounts

All demo accounts share the password in `DEMO_PASSWORD`. The default is
`Booklat@Demo2026!`. It meets the project's 16-character password policy and
avoids the browser weak-password warnings triggered by the old `admin` /
`staff` / `student` passwords.

| LRN | Name | Role |
|-----|------|------|
| `admin` | Demo Administrator | Administrator |
| `staff` | Demo Staff | Staff |
| `student` | Demo Student | Member |
| `202600000001` | Andrea Nicole Villamor | Member |
| `202600000002` | Carlos Joaquin Torres | Member |
| `202600000003` | Danica Marie Salvador | Member |
| `202600000004` | Emmanuel Cabrera | Member |
| `202600000005` | Francesca May Austria | Member |
| `202600000006` | Kristoffer James Manalo | Member |
| `202600000007` | Lorenz Andrei Bautista | Member |
| `202600000008` | Margaux Elise Dimaculangan | Member |
| `202600000009` | Paolo Victor Hernandez | Member |
| `202600000010` | Regine Anne Velasco | Member |
| `202600000011` | Sean Marcus Aguilar | Member |
| `202600000012` | Trixia Joy Labrador | Member |
| `202600000013` | Vincent Rafael Bartolome | Member |
| `202600000014` | Zara Bianca Mercado | Member (suspended) |
| `202600000015` | Juan Miguel Dela Cruz | Member (archived) |

Demo accounts are read-only. `DemoReadOnlyMiddleware` blocks every write
request, prevents demo users from changing their password, and disables the
Users CSV export (which contains password hashes). When `DEMO_MODE=0`, demo
sessions are logged out; run `python manage.py seed_demo` with `DEMO_MODE=0`
to suspend the accounts as well.

## Dataset

- 16 categories, including one archived category
- 62 books (60 active, 2 archived), with 143 physical copies
- 18 users (1 administrator, 1 staff, 16 members)
- 32 loans: 14 active (3 overdue) and 18 returned
- 20 checkout requests across pending, approved, rejected, cancelled, and fulfilled
- 25 Freedom Wall posts: 20 approved, 3 pending, 1 rejected, 1 deleted, plus upvotes
- 4 announcements: 2 active banners and 2 archived
- A generated audit trail covering user, catalog, circulation, moderation, and
  announcement activity

Books include self-help and philosophy titles such as *Atomic Habits*,
*Meditations* by Marcus Aurelius, and *The Way of Zen*, *The Wisdom of
Insecurity*, and *The Book* by Alan Watts, alongside Filipino literature,
fiction, science, history, memoirs, children's books, and reference works.

Book covers use Open Library cover URLs. Missing covers fall back to the
Booklat placeholder image.

## Data files

| File | Contents |
|------|----------|
| `data/categories.json` | Category names and archived state |
| `data/books.json` | Book metadata, cover URLs, copy counts, special copy states |
| `data/users.json` | Demo accounts, roles, statuses, and relative dates |
| `data/loans.json` | Loan history with relative checkout/return offsets |
| `data/requests.json` | Checkout requests and their statuses |
| `data/freedom_posts.json` | Wall posts, moderation state, and upvotes |
| `data/announcements.json` | Active and archived announcements |

Activity dates are relative to the day the seed runs, so overdue loans, recent
returns, and "new arrivals" stay realistic on every deployment. Re-running
`seed_demo` refreshes those relative dates. Celery's automatic Freedom Wall
purge is skipped while `DEMO_MODE=1`, so the wall stays populated between
container restarts.

## Reset

`seed_demo` is idempotent: it updates demo records by stable keys rather than
creating duplicates. To delete only the demo-owned records and rebuild them:

```bash
python manage.py seed_demo --reset
```

The reset removes demo users, books, copies, loans, requests, wall posts,
announcements, audit logs, and any demo category no longer in use. It never
deletes the real superadmin account, roles, permissions, or non-demo books.
Seeding refuses to run if the database already contains non-demo books.

`--reset` requires `DEMO_MODE=1`.
