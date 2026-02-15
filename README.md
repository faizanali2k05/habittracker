# Zenith Habit Tracker

A beautiful, multi-user habit tracker built with Streamlit.

## Setup

1.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the App**:
    ```bash
    streamlit run streamlit_app.py
    ```

## Features

- **User Authentication**: Secure login and registration.
- **Task Management**: Create, track, and complete tasks with due dates and priorities.
- **Habit Tracking**: Monitor daily or weekly habits and build streaks.
- **Dashboard**: Visualize your progress with interactive charts.
- **Calendar View**: See your schedule at a glance.
- **Admin Panel**: Manage users and data (admin role required).

## Local Database

By default, the app uses `habit_tracker.db` (SQLite) in the project root. This is created automatically on first run.

## Hosting on Streamlit Community Cloud

1.  Push this repository to GitHub.
2.  Go to [share.streamlit.io](https://share.streamlit.io/).
3.  Deploy the app by selecting the repository and `streamlit_app.py`.
4.  Add dependencies from `requirements.txt`.
5.  Add secrets (if using a cloud database) directly in Streamlit Cloud settings.

## Database Configuration (Supabase / PostgreSQL)

This app supports PostgreSQL (e.g., Supabase) out of the box.

1.  **Get your Connection String**:
    - Go to your Supabase project settings -> Database -> Connection String.
    - Copy the URI (it looks like `postgres://postgres.xxxx:password@aws-0-region.pooler.supabase.com:6543/postgres`).

2.  **Local Development**:
    - Create a `.env` file in the root directory (or set an environment variable).
    - Add: `DATABASE_URL="your-connection-string"`

3.  **Streamlit Cloud**:
    - Go to your app settings on Streamlit Cloud.
    - Navigate to "Secrets".
    - Add the following TOML configuration:
      ```toml
      DATABASE_URL = "your-connection-string"
      ```

The app will automatically detect the `DATABASE_URL` and switch from SQLite to PostgreSQL.
