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

# --- THEME CONFIGURATION ---
# Only allow dark and light themes
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# --- NOTIFICATION PERMISSION REQUEST ---
# Add notification permission request at the top
if "notification_permission_requested" not in st.session_state:
    st.session_state.notification_permission_requested = False

# Request notification permission with a prominent button
if not st.session_state.notification_permission_requested:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("🔔 **Enable Notifications** for habit reminders and completion alerts!")
        if st.button("Allow Notifications", type="primary", key="notification_perm"):
            st.session_state.notification_permission_requested = True
            st.markdown("""
            <script>
            if ('Notification' in window) {
                Notification.requestPermission().then(function(permission) {
                    console.log('Notification permission:', permission);
                });
            }
            </script>
            """, unsafe_allow_html=True)
            st.success("Notification permission requested! Refresh the page if needed.")
            st.rerun()

# --- CUSTOM CSS FOR RESPONSIVE DESIGN AND THEMES ---
primary_bg = '#0f172a' if st.session_state.theme == 'dark' else '#ffffff'
secondary_bg = '#1e293b' if st.session_state.theme == 'dark' else '#f8fafc'
text_color = '#f8fafc' if st.session_state.theme == 'dark' else '#1e293b'
border_color = '#334155' if st.session_state.theme == 'dark' else '#e2e8f0'

theme_css = f"""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* Apply theme to Streamlit components */
    .stApp {{
        background-color: {primary_bg} !important;
        color: {text_color} !important;
    }}
    
    .stSidebar {{
        background-color: {secondary_bg} !important;
        border-right: 1px solid {border_color} !important;
    }}
    
    .stTextInput input, .stTextArea textarea, .stSelectbox select {{
        background-color: {secondary_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 4px !important;
    }}
    
    .stTextInput label, .stTextArea label, .stSelectbox label {{
        color: {text_color} !important;
    }}
    
    .stButton button {{
        background-color: {secondary_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 4px !important;
    }}
    
    .stButton button:hover {{
        background-color: {border_color} !important;
    }}
    
    .stMarkdown, .stText, p {{
        color: {text_color} !important;
    }}
    
    .stDataFrame, .stTable {{
        background-color: {secondary_bg} !important;
        border: 1px solid {border_color} !important;
    }}
    
    .stDataFrame th, .stTable th {{
        background-color: {border_color} !important;
        color: {text_color} !important;
    }}
    
    .stDataFrame td, .stTable td {{
        color: {text_color} !important;
        border-bottom: 1px solid {border_color} !important;
    }}
    
    .stMetric {{
        background-color: {secondary_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
    }}
    
    .stMetric label {{
        color: {text_color} !important;
    }}
    
    .stMetric .metric-value {{
        color: {text_color} !important;
    }}
    
    .stExpander {{
        background-color: {secondary_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 4px !important;
    }}
    
    .stExpander summary {{
        color: {text_color} !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {secondary_bg} !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {text_color} !important;
    }}
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: {border_color} !important;
    }}

    /* Responsive Design for Mobile */
    @media (max-width: 768px) {{
        .stApp {{
            padding: 1rem !important;
        }}
        
        .stSidebar {{
            width: 100% !important;
            position: relative !important;
        }}
        
        .stColumns {{
            flex-direction: column !important;
        }}
        
        .stMetric {{
            margin-bottom: 1rem !important;
        }}
        
        /* Make buttons larger on mobile */
        .stButton button {{
            width: 100% !important;
            margin-bottom: 0.5rem !important;
        }}
        
        /* Adjust form inputs */
        .stTextInput input, .stTextArea textarea, .stSelectbox select {{
            font-size: 16px !important; /* Prevent zoom on iOS */
        }}
        
        /* Adjust charts for mobile */
        .plotly-chart {{
            height: 300px !important;
        }}
    }}

    /* Typography */
    h1, h2, h3 {{
        font-weight: 600;
        letter-spacing: -0.025em;
        color: {text_color} !important;
    }}
    
    /* Notification styles */
    .notification {{
        position: fixed;
        top: 20px;
        right: 20px;
        background: #22c55e;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    
    @keyframes slideIn {{
        from {{ transform: translateX(100%); opacity: 0; }}
        to {{ transform: translateX(0); opacity: 1; }}
    }}
</style>

<script>
    // Function to show browser notification
    function showBrowserNotification(title, body) {{
        if ('Notification' in window && Notification.permission === 'granted') {{
            new Notification(title, {{
                body: body,
                icon: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iMzIiIGZpbGw9IiMyMmM1NWUiLz4KPHBhdGggZD0iTTI0IDI0SDE2VjE2SDE2VjI0SDE2VjMySDE2VjQwSDE2VjQ4SDE2VjU2SDE2VjY0SDE2VjcySDE2VjgwSDE2VjkySDE2VjEwNFoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=',
                badge: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iMzIiIGZpbGw9IiMyMmM1NWUiLz4KPHBhdGggZD0iTTI0IDI0SDE2VjE2SDE2VjI0SDE2VjMySDE2VjQwSDE2VjQ4SDE2VjU2SDE2VjY0SDE2VjcySDE2VjgwSDE2VjkySDE2VjEwNFoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo='
            }});
        }}
    }}
    
    // Make function globally available
    window.showBrowserNotification = showBrowserNotification;
</script>
"""

st.markdown(theme_css, unsafe_allow_html=True)

# --- NOTIFICATION FUNCTIONS ---
def show_notification(title, message):
    """Show a browser notification"""
    notification_html = f"""
    <div class="notification" id="notification_{hash(title + message)}">
        <strong>{title}</strong><br>
        {message}
    </div>
    <script>
        setTimeout(() => {{
            const notif = document.getElementById('notification_{hash(title + message)}');
            if (notif) notif.remove();
        }}, 4000);
        
        // Also show browser notification if supported
        if (typeof showBrowserNotification !== 'undefined') {{
            showBrowserNotification('{title}', '{message}');
        }}
    </script>
    """
    st.markdown(notification_html, unsafe_allow_html=True)

def check_habit_reminders():
    """Check for habit reminders that are due within 1 hour"""
    user = st.session_state.user
    if not user:
        return
    
    supabase = get_client()
    now = datetime.now()
    one_hour_later = now + timedelta(hours=1)
    
    # Get habits with reminder times
    habits = supabase.table("habits").select("*").eq("user_id", user['id']).execute().data
    
    for habit in habits:
        if habit.get('reminder_time'):
            reminder_time = datetime.strptime(habit['reminder_time'], '%H:%M:%S').time()
            reminder_datetime = datetime.combine(date.today(), reminder_time)
            
            if now <= reminder_datetime <= one_hour_later:
                # Check if already completed today
                today_str = date.today().isoformat()
                completed_today = supabase.table("habit_logs").select("*").eq("habit_id", habit['id']).eq("completed_date", today_str).execute().data
                
                if not completed_today:
                    show_notification(
                        "Habit Reminder", 
                        f"Don't forget to complete your habit: {habit['name']}"
                    )

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
        
        if res.user:
            # Store the session token for authenticated API calls
            if res.session:
                st.session_state.session_token = res.session.access_token
                # Set the auth token for subsequent API calls
                supabase.auth.set_session(res.session.access_token, res.session.refresh_token)
            
            # Safely get role/profile from public.users table
            try:
                # Select only existing columns to avoid errors if schema is out of sync
                user_data = supabase.table("users").select("*").eq("id", res.user.id).single().execute()
                profile = user_data.data
            except Exception:
                # If the profile record doesn't exist, provide a default profile
                profile = {"role": "user"}
            
            return res.user, profile
        return None, None
    except Exception as e:
        # Printing to console for debugging
        print(f"Auth error: {e}")
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
            # Store the session token for authenticated API calls
            if res.session:
                st.session_state.session_token = res.session.access_token
                supabase.auth.set_session(res.session.access_token, res.session.refresh_token)
            
            # Attempt to create user profile in public.users
            try:
                user_payload = {
                    "id": res.user.id,
                    "email": email,
                    "role": "user"
                }
                # Check if full_name column exists (based on current schema it doesn't, but let's be safe)
                # For now, we omit it since we know it causes errors.
                supabase.table("users").insert(user_payload).execute()
            except Exception as profile_err:
                print(f"Profile creation error: {profile_err}")
                # We don't return False here because the auth account WAS created.
                # The user can still log in and we handle missing profiles in login_user.
            
            return True
        return False
    except Exception as e:
        err_msg = str(e).lower()
        if "rate limit" in err_msg:
            st.error("Too many attempts! Please wait a moment.")
            st.warning("💡 TIP: Go to Supabase > Authentication > Providers > Email and **disable 'Confirm email'** to avoid this issue.")
        elif "already registered" in err_msg or "user already exists" in err_msg:
            st.error("User already exists. Please sign in.")
        else:
            st.error(f"Registration Error: {e}")
        return False

# --- SESSION STATES ---
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login" # login or register
if "session_token" not in st.session_state:
    st.session_state.session_token = None

# --- PAGES ---

def login_page():
    # Theme toggle at the top
    col1, col2 = st.columns([4, 1])
    with col2:
        theme_toggle = st.toggle("🌙 Dark", value=st.session_state.theme == "dark", key="theme_toggle_login")
        if theme_toggle != (st.session_state.theme == "dark"):
            st.session_state.theme = "dark" if theme_toggle else "light"
            st.rerun()
    
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
                        # Extract name from metadata or profile
                        display_name = (user_auth.user_metadata.get("full_name") or 
                                       (user_profile.get("full_name") if user_profile else None) or 
                                       email.split("@")[0])
                        
                        st.session_state.user = {
                            "id": user_auth.id, 
                            "email": user_auth.email, 
                            "name": display_name, 
                            "role": user_profile.get("role", "user") if user_profile else "user"
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
            st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
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
        st.plotly_chart(fig2, use_container_width=True, config={'responsive': True})


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
                show_notification("Task Added!", f"New task '{t_title}' has been added to your list.")
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
                        show_notification("Task Completed!", f"Congratulations! You completed: {task['title']}")
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
                show_notification("Habit Added!", f"New habit '{h_name}' has been added to your tracking.")
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
                        show_notification("Habit Completed!", f"Great job! You completed: {h['name']}")
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

# --- MAIN APP LOGIC ---
def main():
    if not st.session_state.user:
        login_page()
    else:
        # Check for habit reminders
        check_habit_reminders()
        
        # Sidebar Navigation
        with st.sidebar:
            st.title("Zenith")
            st.write(f"User: {st.session_state.user['name']}")
            
            # Theme toggle
            theme_toggle = st.toggle("🌙 Dark Mode", value=st.session_state.theme == "dark", key="theme_toggle_main")
            if theme_toggle != (st.session_state.theme == "dark"):
                st.session_state.theme = "dark" if theme_toggle else "light"
                st.rerun()
            
            st.markdown("---")
            
            # Simplified navigation
            page = st.radio("Menu", ["Dashboard", "Tasks", "Habits", "Calendar"])
            
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

if __name__ == "__main__":
    main()
