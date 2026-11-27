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
1. Clone the repo and open the folder
2. python -m venv .venv
3. .venv\Scripts\activate
4. python -m pip install -r requirements.txt
5. Copy .env.example to .env and fill in your own values
6. python manage.py migrate
7. python manage.py createsuperuser
8. python manage.py runserver
9. Open http://127.0.0.1:8000/register/

## Test accounts
- Owner: owner1 / ArtBooth2026Test
- Booth Assistant: assistant1 / ArtBooth2026Test