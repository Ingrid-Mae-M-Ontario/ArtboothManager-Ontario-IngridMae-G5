# ArtBooth Manager

Name: Ingrid Mae M. Ontario
Section: CSIT327-G5

Database-driven web app for artists and small merchandise sellers to manage booths at conventions.
The core feature lets booth owners and assigned assistants record event sales with automatic
stock deduction and voiding. Owners manage items, events, and event stock; assistants can record
sales only at events assigned to them.

## Tech stack
- Django (full stack, Django templates + Bootstrap 5)
- PostgreSQL (Supabase)

## Core feature
- Owners create, view, update, and delete their own catalog items and events, and maintain item
  quantities for each event.
- Item names must be unique per owner and prices must be at least 0.01.
- Event end dates cannot be earlier than start dates.
- Owners assign booth assistants to events. Assistants can record and review their own sales at
  assigned events but cannot manage events or stock.
- A recorded sale snapshots the item price and deducts its quantity from that event's available
  stock. The sale's owner or the assistant who recorded it can void it; voiding restores stock.
- Completed sales are immutable: corrections are made by voiding a sale and recording it again.
- Registration, login/logout, role-based dashboards, and profile editing remain available.

## Setup (Windows PowerShell)
1. Install Python and ensure PostgreSQL/Supabase credentials are available.
2. Clone the repository and open its root folder in PowerShell.
3. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env`, then set `SECRET_KEY`, `DB_NAME`, `DB_USER`,
   `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` to your own Django secret and PostgreSQL/Supabase
   connection values. In PowerShell, copy the example with
   `Copy-Item .env.example .env`. Keep `.env` private; it is ignored by Git.
6. Apply database migrations and optionally create an admin account:
   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```
7. Start the development server:
   ```powershell
   python manage.py runserver
   ```
8. Open http://127.0.0.1:8000/register/ to register, then log in to use the role dashboard.

## Tests
Run the application tests with:
```powershell
python manage.py test
```
