TaskFlow

TaskFlow is a responsive personal productivity application built with Python, Streamlit, and Supabase. It allows users to create individual accounts, manage personal tasks, set weekly goals, reschedule work, and monitor completion progress from desktop, tablet, or mobile devices.

Features

Secure email and password account registration

User sign-in and sign-out

Personal task storage for every account

Add, view, edit, complete, reopen, reschedule, and delete tasks

Low, medium, and high task priorities

Today, upcoming, and overdue task views

Search and filter tasks by status, priority, and date

Create and manage weekly goals

Set a target completion date for each goal

Reschedule goals to another week

Dashboard statistics and completion rates

Responsive corporate-style interface

Supabase Row Level Security for user data isolation

Technology

Python

Streamlit

Supabase Authentication

Supabase PostgreSQL Database

HTML and CSS

Project Structure

taskflow/
├── .streamlit/
│   └── secrets.toml
├── assets/
│   └── style.css
├── app.py
├── auth.py
├── database.py
├── goal_manager.py
├── task_manager.py
├── supabase_schema.sql
├── requirements.txt
├── .gitignore
└── README.md

The .streamlit/secrets.toml file is required locally but must never be uploaded to GitHub.

Local Installation

Clone the repository:

git clone https://github.com/Clinntech/taskflow.git
cd taskflow

Create a virtual environment:

Windows:

python -m venv venv
venv\Scripts\activate

Linux and macOS:

python3 -m venv venv
source venv/bin/activate

Install the required packages:

pip install -r requirements.txt

Supabase Setup

Create a Supabase project and run the contents of supabase_schema.sql in the Supabase SQL Editor.

The script creates:

A tasks table

A weekly_goals table

Database indexes

Automatic update and completion timestamps

Row Level Security policies

User-specific create, read, update, and delete permissions

Create a .streamlit folder in the project directory. Inside it, create secrets.toml:

[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
publishable_key = "sb_publishable_YOUR_KEY"

Use the Supabase publishable key. Never use a secret key or service role key in this application.

Confirm that .gitignore contains:

.streamlit/secrets.toml

Running the Application

Start Streamlit from the project directory:

streamlit run app.py

Open the local address displayed in the terminal, normally:

http://localhost:8501

Testing User Privacy

To confirm that Row Level Security is working:

Create and sign in to the first account.

Add a task and a weekly goal.

Sign out.

Create or sign in to a second account.

Confirm that the second account cannot see the first account's data.

Streamlit Community Cloud Deployment

Upload the project to a public GitHub repository.

Sign in to Streamlit Community Cloud.

Create a new application from the GitHub repository.

Set app.py as the application entry point.

Open the application's Secrets settings.

Add the same Supabase configuration used locally.

Deploy the application.

Do not upload secrets.toml to GitHub. Streamlit deployment credentials must be entered through the Community Cloud Secrets settings.

Security

TaskFlow uses Supabase Authentication and PostgreSQL Row Level Security. Each task and weekly goal is linked to the authenticated user's unique identifier. Database policies restrict authenticated users to their own records.

Users should choose strong passwords and avoid sharing account credentials. Production deployments should also configure email confirmation, permitted redirect URLs, password recovery, and appropriate Supabase authentication settings.

Integration and Embedding

TaskFlow may be linked to or embedded within compatible websites, productivity platforms, and internal business applications. Any integration must follow the terms, privacy requirements, security policies, licensing conditions, and authorization procedures of the platforms involved.

The source code may not be copied, redistributed, rebranded, sold, or used commercially without permission from the project owner unless a separate license explicitly permits that use.

Contact

Email: clintechke@gmail.com

GitHub: https://github.com/Clinntech

Portfolio: https://clinntech.github.io/Clinton-Mutinda/

Copyright

Copyright 2026 Clinntech. All rights reserved.

Permission is required for commercial use, redistribution, rebranding, or integration outside the usage allowed by an applicable repository license.
