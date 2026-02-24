# Bike Team Rides App

A Shiny for Python application for managing Bike MS training rides, registrations, team rosters, and email notifications.

## Overview

This application provides a lightweight ride management system for cycling teams participating in Bike MS events. It supports ride creation, rider signups, cancellation via confirmation codes, roster viewing, and optional team notification workflows.

The application uses a SQLite backend and automatically initializes its database on first run.

## Features

- Create and manage training rides
- Rider registration with unique confirmation code
- Cancel registration using confirmation number
- View roster by ride and date
- Admin-protected ride creation and deletion
- Email notification preparation for team mailing list
- Automatic database and table creation

## Technology Stack

- Python
- Shiny for Python
- SQLite
- Pandas

## Project Structure

```
app.py              Main Shiny application
database.py         Database connection and CRUD logic
requirements.txt    Python dependencies
schema.sql          Database schema (optional reference)
team_photo.png      UI image asset
.gitignore          Prevents private files from being committed
```

## Installation

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

The database file will be created automatically inside a local `data/` directory.

## Configuration

The admin password is defined in the application. For production use, it is recommended to move this to an environment variable.

The optional mailing list feature looks for a file named:

```
contacts.csv
```

If this file is not present, the notification feature will be disabled automatically.

## Privacy Notice

This repository does not contain any real rider data, mailing lists, or database files. The SQLite database and contact files are intentionally excluded from version control.

## Author

Evelyn Tadlock
