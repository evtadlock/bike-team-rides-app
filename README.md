# Bike Team Rides App

A Shiny for Python application for managing Bike MS training rides, registrations, team rosters, and notifications.

This app was developed to support Team Ugly training rides leading up to Bike MS events.

---

## Overview

The application provides a centralized system where riders can:

- View scheduled training rides
- Sign up for rides
- Cancel their registration
- View ride rosters

Admins can create, notify, and manage rides through a password-protected panel.

The application uses a SQLite backend that initializes automatically on first run.

---

## Rider Instructions

### 1. Signing Up for a Ride

1. Open the application link provided by the team.
2. Navigate to the **Sign Up** tab.
3. Select a ride from the ride list.
4. Enter your full name.
5. Click **Sign Up**.

After registering, you will receive a confirmation number.

Save this number. It is required if you need to cancel your spot.

---

### 2. Cancelling a Ride Registration

1. Go to the **Cancel Registration** tab.
2. Enter your confirmation number.
3. Click **Cancel My Spot**.

If the code is valid, your registration will be removed.

---

### 3. Viewing the Ride Roster

1. Navigate to the **Roster** tab.
2. View riders signed up by ride and date.

---

## Admin Instructions

Admin access is password protected.

### Creating a Ride

1. Open the **Admin** tab.
2. Enter the admin password.
3. Complete the ride form:
   - Ride Name
   - Date
   - Start Time
   - Meeting Point
   - GPS Route Link
4. Click **Create Ride**.

---

### Notifying the Team

1. Select a ride in the notification section.
2. Click **Prepare Notification**.
3. Choose:
   - Gmail
   - Email App
   - Copy Email List

This feature requires a `contacts.csv` mailing list file.

---

### Deleting a Ride

1. Select a ride from the delete dropdown.
2. Click **Delete Ride**.

This removes both the ride and associated signups.

---

## Technology Stack

- Python
- Shiny for Python
- SQLite
- Pandas

---

## Installation (Developers)

Clone the repository:

```
git clone https://github.com/evtadlock/bike-team-rides-app.git
cd bike-team-rides-app
```

Install dependencies:

```
pip install -r requirements.txt
```

Run the application:

```
shiny run app.py
```

The database will be created automatically in a local `data/` directory.

---

## Optional Mailing List File

To enable notifications, add a file named:

```
contacts.csv
```

Example format:

```
First Name,Email
Jane,jane@example.com
John,john@example.com
```

This file is excluded from version control for privacy reasons.

---

## Privacy Notice

This repository does not contain real rider data, mailing lists, or database files. All personal data is excluded from version control.

---

## Author

Evelyn Tadlock
