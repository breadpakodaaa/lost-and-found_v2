# Campus Lost & Found — Version 2

This started as my Python course project idea: a place for lost campus belongings to find their way home. Version 1 was the starting point; Version 2 has had a rather enthusiastic upgrade. It now includes student accounts, authentication and authorisation, an admin area, item claims, and a fuzzy matching feature that tries to connect the lost reports with the found ones. It is still a learning project, so the matches are suggestions for people to review.

## Run locally

Install the dependencies from this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

The app needs a private `SECRET_KEY`. Generate one with:

```powershell
py -c "import secrets; print(secrets.token_hex(32))"
```

Create a `.env` file in the project folder and add the generated key and local database settings:

```text
SECRET_KEY=paste-your-generated-key-here
DATABASE_URL=sqlite:///campus_lost_found.db
SESSION_COOKIE_SECURE=false
```

Keep `.env` private; Git ignores it. Start the app with:

```powershell
py run.py
```

Then open `http://127.0.0.1:5000/` in your browser.

## Features

- **Accounts and access:** Students can register, sign in, and sign out. Passwords are stored as hashes. Sign-in is required for reporting items and submitting claims, and users can edit or remove only their own listings.
- **Lost and found reports:** Create a report with an item name, description, category, location, date, colour, and optional image.
- **Browse and search:** Browse all, lost, or found reports. Filter listings by name, category, location, and date.
- **Possible matches:** Review suggestions between active lost reports and available found reports, with an overall score and a breakdown of the matching factors.
- **Claims:** If a found item looks familiar, submit a claim with an explanation and identifying details. Claims stay pending until an administrator reviews them.
- **Student dashboard:** See your listings, the claims you submitted, claims on your found listings, and links to possible matches. Edit or remove your own reports here.
- **Admin dashboard:** Administrators can view users, listings, and claims; approve or reject claims; update item statuses; and remove listings.
- **Status tracking:** Lost reports can be active, matched, or resolved. Found reports can be available, claimed, or returned. Only active lost and available found reports are considered for new match suggestions.
- **Basic web security:** Forms use CSRF protection, uploads are limited and checked, and private identifying details are not displayed on public listings.

## How matching works

The matching service uses RapidFuzz to compare text after normalising it: text is lowercased, accents and punctuation are removed, and spacing is cleaned up. RapidFuzz’s `WRatio` score helps account for small spelling differences and words appearing in a different order.

Each eligible lost/found pair receives a score from 0 to 100 using these weights:

| Factor | Weight | How it is compared |
| --- | ---: | --- |
| Item name | 30% | Fuzzy text similarity |
| Description | 25% | Fuzzy text similarity |
| Category | 15% | Exact match after normalisation |
| Colour | 10% | Fuzzy text similarity |
| Location | 10% | Fuzzy text similarity |
| Date | 10% | Closer dates score higher, up to the configured date window |

Missing details score zero; they do not make the other factors count for more. Date similarity decreases as the gap grows and becomes zero outside the configured window. The default window is 30 days.

By default, scores below 50% are not shown. Scores from 50–69% are labelled weak, 70–89% possible, and 90–100% very strong. The weights, date window, and score thresholds can be adjusted in `config.py`.

These scores are just clues. A high score does not prove that two reports describe the same object; a person should review the details and handle any claim.

## Screenshots

Add screenshots of the running app below:

### Home page

_Screenshot placeholder: home page_

### Browse and search

_Screenshot placeholder: browse listings and filters_

### Match suggestions

_Screenshot placeholder: possible matches and score breakdown_

### Student dashboard

_Screenshot placeholder: student dashboard_

### Admin dashboard

_Screenshot placeholder: admin dashboard and claim review_
