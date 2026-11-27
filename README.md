# ArtBooth Manager

Name: Ingrid Mae M. Ontario
Section: CSIT327-G5

Database-driven web app for artists and small merchandise sellers to manage booths at conventions.

## Features
- Account Feature (PD1): registration, login/logout, role-based dashboards (Owner and Booth Assistant), and user profile.
- Core Feature (PD2): Sales Recording with automatic stock deduction.

## Core Feature: Sales Recording
Owners create items and events, assign per-event stock, and record sales.
Booth Assistants assigned to an event can record sales for it.
Each sale validates stock, deducts it automatically, saves the unit price at the time of sale,
computes the total, and records the payment method. A completed sale can be voided by the Owner,
which restores the stock. Sales can only be recorded while the event is Ongoing.

## Tech stack
- Django (full stack, Django templates + Bootstrap 5)
- PostgreSQL (Supabase)

## How to run
1. Clone the repository and open the project folder.
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`, then fill in the database credentials and secret key.
5. Apply migrations:
   ```powershell
   python manage.py migrate
   ```
6. Create an administrator account:
   ```powershell
   python manage.py createsuperuser
   ```
7. Start the server:
   ```powershell
   python manage.py runserver
   ```
8. Open <http://127.0.0.1:8000/register/> or <http://127.0.0.1:8000/login/>.

Never commit `.env`; it is excluded by `.gitignore`.

## Run automated tests

```powershell
python manage.py test
```

To run tests for each app separately:

```powershell
python manage.py test accounts
python manage.py test booth
```

## Test accounts
- Owner: owner1 / ArtBooth2026Test
- Booth Assistant: assistant1 / ArtBooth2026Test