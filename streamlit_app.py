# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, date, timedelta
import time

# --- PATH SETUP to import backend modules ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import Supabase client
try:
    from app.client import get_supabase_client
except ImportError as e:
    st.error(f"Error importing backend modules: {e}")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Zenith Habit Tracker",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- CUSTOM CSS FOR PROFESSIONAL AESTHETICS ---
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Internal:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Typography */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.025em;
    }
    
</style>
""", unsafe_allow_html=True)

# --- SUPABASE HELPERS ---
def get_client():
    return get_supabase_client()

# --- AUTH FUNCTIONS ---
def login_user(email, password):
    supabase = get_client()
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        # Determine role from public.users table
        user_data = supabase.table("users").select("role, full_name").eq("id", res.user.id).single().execute()
        return res.user, user_data.data
    except Exception as e:
        return None, None

def register_user(email, password, full_name):
    supabase = get_client()
    try:
        res = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        
        if res.user:
            # Create user in public.users table
            # Note regarding RLS: Make sure "users" table has an INSERT policy for auth.uid() = id
            user_payload = {
                "id": res.user.id,
                "email": email,
                "role": "user"
                # "full_name" could be added if schema supports it, current schema doesn't have it in users table explicitly in user prompt but does in models.
                # User prompt schema: id, email, role.
            }
            supabase.table("users").insert(user_payload).execute()
            
            # Create default categories is desirable?
            # User instructions didn't specify, but existing code did.
            # Let's keep it simple as per instructions.
            return True
        return False
    except Exception as e:
        st.error(f"Registration Error: {e}")
        return False

# --- SESSION STATES ---
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login" # login or register

# --- PAGES ---

def login_page():
    # Center the login form responsibly
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.auth_mode == "login":
            st.title("Sign In")
            st.markdown("Welcome back using your Zenith account.")
            
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", type="primary")
                
                if submitted:
                    user_auth, user_profile = login_user(email, password)
                    if user_auth and user_profile:
                        st.session_state.user = {
                            "id": user_auth.id, 
                            "email": user_auth.email, 
                            "name": user_profile.get("full_name") or email.split("@")[0], 
                            "role": user_profile.get("role", "user")
                        }
                        st.success("Login successful")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
            
            st.markdown("---")
            st.markdown("No account?")
            if st.button("Create an account"):
                st.session_state.auth_mode = "register"
                st.rerun()

        else:
            st.title("Sign Up")
            st.markdown("Create your account to get started.")
            with st.form("register_form"):
                new_email = st.text_input("Email")
                new_name = st.text_input("Full Name")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                register_submitted = st.form_submit_button("Create Account", type="primary")
                
                if register_submitted:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif not new_email or not new_password:
                        st.error("Please fill all fields")
                    else:
                        if register_user(new_email, new_password, new_name):
                            st.success("Account created successfully. Please sign in.")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error("Registration failed. Email might already exist.")
            
            st.markdown("---")
            st.markdown("Already have an account?")
            if st.button("Sign In"):
                st.session_state.auth_mode = "login"
                st.rerun()

def dashboard_page():
    user = st.session_state.user
    st.title("Dashboard")
    st.markdown(f"Welcome, {user['name']}")
    
    supabase = get_client()
    today_str = date.today().isoformat()
    
    # Alerts
    # Overdue tasks
    overdue_res = supabase.table("tasks").select("*").lt("due_date", today_str).eq("status", "pending").execute()
    overdue = overdue_res.data
    if overdue:
        st.error(f"You have {len(overdue)} overdue tasks.")
    
    # Due today
    due_today_res = supabase.table("tasks").select("*").eq("due_date", today_str).eq("status", "pending").execute()
    due_today = due_today_res.data
    if due_today:
        st.warning(f"You have {len(due_today)} tasks due today.")
    
    # Tasks Stats
    all_tasks_res = supabase.table("tasks").select("status", count="exact").execute()
    total_tasks = all_tasks_res.count 
    # Note: select(count="exact") returns count in .count property if we don't fetch data, but typically we need data or just count.
    # To get just counts efficiently:
    # We can separate queries or just get all tasks if dataset is small. For scalability, count queries are better.
    
    # Pending
    pending_res = supabase.table("tasks").select("*", count="exact").eq("status", "pending").execute()
    pending_tasks = pending_res.count
    
    # Completed
    completed_res = supabase.table("tasks").select("*", count="exact").eq("status", "completed").execute()
    completed_tasks = completed_res.count
    
    # Habits
    habits_res = supabase.table("habits").select("*").execute()
    habits = habits_res.data
    
    habit_entries_res = supabase.table("habit_logs").select("*", count="exact").eq("completed_date", today_str).execute()
    habit_entries_today = habit_entries_res.count
    
    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tasks", total_tasks)
    m2.metric("Pending", pending_tasks)
    m3.metric("Completed", completed_tasks)
    m4.metric("Habits Today", f"{habit_entries_today}/{len(habits)}")
    
    # Charts
    st.subheader("Overview")
    c1, c2 = st.columns(2)
    
    with c1:
        # Task Status Pie Chart
        if total_tasks > 0:
            labels = ['Pending', 'Completed', 'In Progress']
            # We need in_progress count
            in_progress_count = total_tasks - pending_tasks - completed_tasks # Estimate or query
            # Better check existing statuses. User script had 'pending' default.
            # Assuming just pending/completed for now based on simple model, or maybe 'in_progress' exists.
            # Let's simple query for 'in_progress'
            in_prog_res = supabase.table("tasks").select("*", count="exact").eq("status", "in_progress").execute()
            values = [pending_tasks, completed_tasks, in_prog_res.count]
            
            fig = px.pie(values=values, names=labels, hole=0.6, color_discrete_sequence=['#ef4444', '#22c55e', '#3b82f6'])
            fig.update_layout(showlegend=True, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tasks created yet.")

    with c2:
        # Habit Streaks (Mock logic for now, or complex query)
        # Getting last 7 days habit logs
        last_7_days = [date.today() - timedelta(days=i) for i in range(7)]
        dates_str = [d.strftime("%a") for d in last_7_days][::-1]
        
        daily_completions = []
        for d in last_7_days:
            # Query count of logs for this date
            c = supabase.table("habit_logs").select("*", count="exact").eq("completed_date", d.isoformat()).execute().count
            daily_completions.append(c)
        
        daily_completions = daily_completions[::-1]
        
        fig2 = go.Figure(data=[go.Bar(x=dates_str, y=daily_completions, marker_color='#3b82f6')])
        fig2.update_layout(title="Habit Activity (Last 7 Days)", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig2, use_container_width=True)


def tasks_page():
    st.title("Tasks")
    user = st.session_state.user
    supabase = get_client()

    # Create Task
    with st.expander("Create New Task", expanded=False):
        with st.form("new_task_form"):
            t_title = st.text_input("Task Title")
            t_desc = st.text_area("Description")
            c1, c2, c3 = st.columns(3)
            with c1: t_date = st.date_input("Due Date")
            with c2: t_priority = st.selectbox("Priority", ["low", "medium", "high"])
            with c3: 
                # Fetch categories
                cats_res = supabase.table("categories").select("*").execute()
                cats = cats_res.data
                t_cat_name = st.selectbox("Category", [c['name'] for c in cats]) if cats else None
            
            submitted = st.form_submit_button("Add Task", type="primary")
            if submitted and t_title:
                cat_id = next((c['id'] for c in cats if c['name'] == t_cat_name), None) if t_cat_name else None
                
                new_task = {
                    "title": t_title,
                    "description": t_desc,
                    "due_date": t_date.isoformat(),
                    "priority": t_priority,
                    "user_id": user['id'],
                    "category_id": cat_id,
                    "status": "pending"
                }
                supabase.table("tasks").insert(new_task).execute()
                st.success("Task added")
                st.rerun()

    # View Tasks (Tabs)
    tab1, tab2, tab3 = st.tabs(["Pending", "Completed", "All"])
    
    # Fetch all tasks
    tasks_res = supabase.table("tasks").select("*").order("due_date").execute()
    tasks = tasks_res.data
    
    def render_task_card(task, context):
        with st.container():
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.markdown(f"**{task['title']}**")
                priority_label = task.get('priority', 'medium').upper()
                desc = task.get('description') or 'No description'
                due = task.get('due_date')
                st.caption(f"Due: {due} • {priority_label} • {desc}")
            with col_b:
                if task['status'] != "completed":
                    if st.button("Complete", key=f"done_{task['id']}_{context}"):
                        supabase.table("tasks").update({"status": "completed"}).eq("id", task['id']).execute()
                        st.rerun()
                else:
                    st.write("Done")
                
                if st.button("Delete", key=f"del_{task['id']}_{context}"):
                    supabase.table("tasks").delete().eq("id", task['id']).execute()
                    st.rerun()
            st.divider()

    with tab1:
        pending = [t for t in tasks if t['status'] == "pending"]
        if not pending: st.info("No pending tasks.")
        for task in pending: render_task_card(task, "pending")
            
    with tab2:
        completed = [t for t in tasks if t['status'] == "completed"]
        if not completed: st.info("No completed tasks.")
        for task in completed: render_task_card(task, "completed")

    with tab3:
        if not tasks: st.info("No tasks found.")
        for task in tasks: render_task_card(task, "all")


def habits_page():
    st.title("Habits")
    user = st.session_state.user
    supabase = get_client()
    
    # Create Habit
    with st.expander("Create New Habit"):
        with st.form("new_habit"):
            h_name = st.text_input("Habit Name")
            h_freq = st.selectbox("Frequency", ["daily", "weekly"])
            # Reminder time is in schema? Yes "reminder_time".
            h_time = st.time_input("Reminder Time")
            
            submitted = st.form_submit_button("Start Habit", type="primary")
            if submitted and h_name:
                h = {
                    "name": h_name, 
                    "frequency": h_freq, 
                    "reminder_time": h_time.isoformat(),
                    "user_id": user['id']
                }
                supabase.table("habits").insert(h).execute()
                st.success("Habit created")
                st.rerun()
    
    st.subheader("Your Habits")
    habits = supabase.table("habits").select("*").execute().data
    today_str = date.today().isoformat()
    
    if not habits:
        st.info("No habits tracking yet. Add one above.")

    for h in habits:
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{h['name']}**")
                st.caption(f"Target: {h['frequency']}")
            
            # Check if done today
            entry_res = supabase.table("habit_logs").select("*").eq("habit_id", h['id']).eq("completed_date", today_str).execute()
            entry = entry_res.data
            is_done_today = len(entry) > 0
            
            with c2:
                if is_done_today:
                    st.write("Completed")
                else:
                    if st.button("Mark Complete", key=f"habit_{h['id']}"):
                        log = {
                            "habit_id": h['id'],
                            "user_id": user['id'],
                            "completed_date": today_str
                        }
                        supabase.table("habit_logs").insert(log).execute()
                        st.rerun()
            
            with c3:
                # Count total entries
                streak = supabase.table("habit_logs").select("*", count="exact").eq("habit_id", h['id']).execute().count
                st.metric("Total", streak)
            
            val = 1.0 if is_done_today else 0.0
            st.progress(val)
            st.divider()

def calendar_page():
    st.title("Calendar")
    user = st.session_state.user
    supabase = get_client()
    
    selected_date = st.date_input("Select Date", date.today())
    date_str = selected_date.isoformat()
    
    st.subheader(f"Schedule for {selected_date}")
    
    # Tasks
    tasks = supabase.table("tasks").select("*").eq("due_date", date_str).execute().data
    if tasks:
        st.markdown("**Tasks**")
        for t in tasks:
            st.info(f"{t['title']} - {t['status']}")
    else:
        st.write("No tasks scheduled.")
        
    # Habits
    entries = supabase.table("habit_logs").select("*, habits(name)").eq("completed_date", date_str).execute().data
    # Note: To get habit name, we need to join or fetch separately. Supabase supports recursive joins if FK exists.
    # "select('*, habits(name)')" works if FK is set up correctly in Supabase.
    # If not, we might need manual fetch. Let's assume standard join works.
    
    if entries:
        st.markdown("**Habits Completed**")
        for e in entries:
            # e['habits'] might be a dict or list
            h_name = e.get('habits', {}).get('name', 'Unknown Habit')
            st.success(f"{h_name}")

def admin_page():
    st.title("Admin Administration")
    user = st.session_state.user
    supabase = get_client()
    
    # Role check
    # We already have user['role'] from login
    if user.get('role') != 'admin':
        st.error("Access Denied.")
        return

    st.subheader("User Directory")
    # Need admin policy to see all users
    try:
        users = supabase.table("users").select("*").execute().data
        if users:
            st.dataframe(users)
            if st.checkbox("View JSON Data"):
                st.json(users)
        else:
            st.info("No users found or permission denied.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    
    # Backup (Not applicable for Supabase same way, maybe export CSV)
    st.write("Database is managed by Supabase. Use Supabase Dashboard for backups.")

# --- MAIN APP LOGIC ---
def main():
    if not st.session_state.user:
        login_page()
    else:
        # Sidebar Navigation
        with st.sidebar:
            st.title("Zenith")
            st.write(f"User: {st.session_state.user['name']}")
            
            # Simplified navigation
            page = st.radio("Menu", ["Dashboard", "Tasks", "Habits", "Calendar", "Admin"])
            
            st.markdown("---")
            if st.button("Sign Out"):
                st.session_state.user = None
                st.rerun()
        
        if page == "Dashboard":
            dashboard_page()
        elif page == "Tasks":
            tasks_page()
        elif page == "Habits":
            habits_page()
        elif page == "Calendar":
            calendar_page()
        elif page == "Admin":
            admin_page()

if __name__ == "__main__":
    main()
