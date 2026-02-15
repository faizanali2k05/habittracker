# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, date, timedelta
import time
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract

# --- PATH SETUP to import backend modules ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from app.database import SessionLocal, init_db, engine, Base
    from app.models import User, Task, Habit, HabitEntry, Category, TaskCategory
    from app.auth import hash_password, verify_password, create_access_token
except ImportError as e:
    st.error(f"Error importing backend modules: {e}")
    st.stop()

# --- INITIALIZE DB ---
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    st.error(f"Database initialization error: {e}")

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

# --- DB HELPERS ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTH FUNCTIONS ---
def login_user(email, password):
    db: Session = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.password):
        return user
    return None

def register_user(email, password, full_name):
    db: Session = next(get_db())
    if db.query(User).filter(User.email == email).first():
        return False # User exists
    new_user = User(
        email=email,
        password=hash_password(password),
        full_name=full_name,
        role="user" 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create default categories
    default_cats = ["Work", "Study", "Personal", "Health"]
    colors = ["#3B82F6", "#8B5CF6", "#F43F5E", "#10B981"]
    for i, cat_name in enumerate(default_cats):
        cat = TaskCategory(name=cat_name, user_id=new_user.id, color=colors[i])
        db.add(cat)
        
        h_cat = Category(name=cat_name, user_id=new_user.id, color=colors[i])
        db.add(h_cat)
        
    db.commit()
    return True

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
                    user = login_user(email, password)
                    if user:
                        st.session_state.user = {"id": user.id, "email": user.email, "name": user.full_name, "role": user.role}
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
                            st.error("Email already exists")
            
            st.markdown("---")
            st.markdown("Already have an account?")
            if st.button("Sign In"):
                st.session_state.auth_mode = "login"
                st.rerun()

def dashboard_page():
    user = st.session_state.user
    st.title("Dashboard")
    st.markdown(f"Welcome, {user['name']}")
    
    db: Session = next(get_db())
    today = date.today()
    
    # Alerts
    overdue = db.query(Task).filter(Task.user_id == user['id'], Task.due_date < today, Task.status == "pending").all()
    if overdue:
        st.error(f"You have {len(overdue)} overdue tasks.")
    
    due_today = db.query(Task).filter(Task.user_id == user['id'], Task.due_date == today, Task.status == "pending").all()
    if due_today:
        st.warning(f"You have {len(due_today)} tasks due today.")
    
    # Tasks
    total_tasks = db.query(Task).filter(Task.user_id == user['id']).count()
    pending_tasks = db.query(Task).filter(Task.user_id == user['id'], Task.status == "pending").count()
    completed_tasks = db.query(Task).filter(Task.user_id == user['id'], Task.status == "completed").count()
    
    # Habits
    habits = db.query(Habit).filter(Habit.user_id == user['id']).all()
    habit_entries_today = db.query(HabitEntry).join(Habit).filter(Habit.user_id == user['id'], HabitEntry.date == today).count()
    
    # Metrics
    # Use columns that wrap nicely on mobile (streamlit handles this)
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
            values = [
                pending_tasks, 
                completed_tasks,
                db.query(Task).filter(Task.user_id == user['id'], Task.status == "in_progress").count()
            ]
            fig = px.pie(values=values, names=labels, hole=0.6, color_discrete_sequence=['#ef4444', '#22c55e', '#3b82f6'])
            fig.update_layout(
                showlegend=True,
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tasks created yet.")

    with c2:
        # Habit Streaks
        last_7_days = [today - timedelta(days=i) for i in range(7)]
        dates_str = [d.strftime("%a") for d in last_7_days][::-1]
        
        daily_completions = []
        for d in last_7_days:
            count = db.query(HabitEntry).join(Habit).filter(Habit.user_id == user['id'], HabitEntry.date == d).count()
            daily_completions.append(count)
        
        daily_completions = daily_completions[::-1]
        
        fig2 = go.Figure(data=[go.Bar(x=dates_str, y=daily_completions, marker_color='#3b82f6')])
        fig2.update_layout(
            title="Habit Activity (Last 7 Days)",
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)


def tasks_page():
    st.title("Tasks")
    user = st.session_state.user
    db: Session = next(get_db())

    # Create Task
    with st.expander("Create New Task", expanded=False):
        with st.form("new_task_form"):
            t_title = st.text_input("Task Title")
            t_desc = st.text_area("Description")
            c1, c2, c3 = st.columns(3)
            with c1: t_date = st.date_input("Due Date")
            with c2: t_time = st.time_input("Due Time")
            with c3: t_priority = st.selectbox("Priority", ["low", "medium", "high"])
            
            cats = db.query(TaskCategory).filter(TaskCategory.user_id == user['id']).all()
            t_cat = st.selectbox("Category", [c.name for c in cats]) if cats else None
            
            submitted = st.form_submit_button("Add Task", type="primary")
            if submitted and t_title:
                cat_id = next((c.id for c in cats if c.name == t_cat), None) if t_cat else None
                new_task = Task(
                    title=t_title,
                    description=t_desc,
                    due_date=t_date,
                    due_time=t_time,
                    priority=t_priority,
                    user_id=user['id'],
                    category_id=cat_id,
                    status="pending"
                )
                db.add(new_task)
                db.commit()
                st.success("Task added")
                st.rerun()

    # View Tasks (Tabs)
    tab1, tab2, tab3 = st.tabs(["Pending", "Completed", "All"])
    
    tasks = db.query(Task).filter(Task.user_id == user['id']).order_by(Task.due_date).all()
    
    def render_task_card(task, context):
        with st.container():
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.markdown(f"**{task.title}**")
                # Removed emojis and made it cleaner
                priority_label = task.priority.upper()
                st.caption(f"Due: {task.due_date} {task.due_time} • {priority_label} • {task.description or 'No description'}")
            with col_b:
                if task.status != "completed":
                    if st.button("Complete", key=f"done_{task.id}_{context}"):
                        task.status = "completed"
                        task.completed_at = datetime.now()
                        db.commit()
                        st.rerun()
                else:
                    st.write("Done")
                
                if st.button("Delete", key=f"del_{task.id}_{context}"):
                    db.delete(task)
                    db.commit()
                    st.rerun()
            st.divider()

    with tab1:
        pending = [t for t in tasks if t.status == "pending"]
        if not pending:
            st.info("No pending tasks.")
        for task in pending:
            render_task_card(task, "pending")
            
    with tab2:
        completed = [t for t in tasks if t.status == "completed"]
        if not completed:
            st.info("No completed tasks.")
        for task in completed:
            render_task_card(task, "completed")

    with tab3:
        if not tasks:
            st.info("No tasks found.")
        for task in tasks:
            render_task_card(task, "all")


def habits_page():
    st.title("Habits")
    user = st.session_state.user
    db: Session = next(get_db())
    
    # Create Habit
    with st.expander("Create New Habit"):
        with st.form("new_habit"):
            h_name = st.text_input("Habit Name")
            h_freq = st.selectbox("Frequency", ["daily", "weekly"])
            submitted = st.form_submit_button("Start Habit", type="primary")
            if submitted and h_name:
                h = Habit(title=h_name, frequency=h_freq, user_id=user['id'])
                db.add(h)
                db.commit()
                st.success("Habit created")
                st.rerun()
    
    st.subheader("Your Habits")
    habits = db.query(Habit).filter(Habit.user_id == user['id']).all()
    today = date.today()
    
    if not habits:
        st.info("No habits tracking yet. Add one above.")

    for h in habits:
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{h.title}**")
                st.caption(f"Target: {h.frequency}")
            
            # Check if done today
            entry = db.query(HabitEntry).filter(HabitEntry.habit_id == h.id, HabitEntry.date == today).first()
            is_done_today = entry is not None
            
            with c2:
                if is_done_today:
                    st.write("Completed")
                else:
                    if st.button("Mark Complete", key=f"habit_{h.id}"):
                        entry = HabitEntry(habit_id=h.id, date=today, completed=True)
                        db.add(entry)
                        db.commit()
                        st.rerun()
            
            with c3:
                streak = db.query(HabitEntry).filter(HabitEntry.habit_id == h.id).count() 
                st.metric("Total", streak)
            
            val = 1.0 if is_done_today else 0.0
            st.progress(val)
            st.divider()

def calendar_page():
    st.title("Calendar")
    user = st.session_state.user
    db: Session = next(get_db())
    
    selected_date = st.date_input("Select Date", date.today())
    
    st.subheader(f"Schedule for {selected_date}")
    
    # Tasks for this date
    tasks = db.query(Task).filter(Task.user_id == user['id'], Task.due_date == selected_date).all()
    if tasks:
        st.markdown("**Tasks**")
        for t in tasks:
            st.info(f"{t.title} - {t.status}")
    else:
        st.write("No tasks scheduled.")
        
    # Habit entries for this date
    entries = db.query(HabitEntry).join(Habit).filter(Habit.user_id == user['id'], HabitEntry.date == selected_date).all()
    if entries:
        st.markdown("**Habits Completed**")
        for e in entries:
            st.success(f"{e.habit.title}")

def admin_page():
    st.title("Admin Administration")
    user = st.session_state.user
    if user['role'] != 'admin':
        st.error("Access Denied.")
        return

    db: Session = next(get_db())
    
    st.subheader("User Directory")
    users = db.query(User).all()
    
    user_data = [{"ID": u.id, "Email": u.email, "Name": u.full_name, "Role": u.role} for u in users]
    st.dataframe(user_data, use_container_width=True)
    
    st.subheader("Data Export")
    if st.checkbox("View JSON Data"):
        st.json(user_data)
    
    # Backup
    db_path = "habit_tracker.db" 
    if os.path.exists(db_path):
        with open(db_path, "rb") as f:
            st.download_button("Download Database Backup", f, file_name="habit_tracker_backup.db")

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
