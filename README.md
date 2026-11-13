# ArtBooth Manager

Name: Ingrid Mae M. Ontario
Section: CSIT327-G5

Database-driven web app for artists and small merchandise sellers to manage booths at conventions.
This phase covers the Account Feature: registration, login/logout, role-based dashboards
(Owner and Booth Assistant), and user profile.

## Tech stack
- Django (full stack, Django templates + Bootstrap 5)
- PostgreSQL (Supabase)

## How to run
1. Clone the repo and open the folder
2. python -m venv .venv
3. .venv\Scripts\activate
4. pip install -r requirements.txt
5. Copy .env.example to .env and fill in your own values
6. python manage.py migrate
7. python manage.py createsuperuser
8. python manage.py runserver
9. Open http://127.0.0.1:8000/register/