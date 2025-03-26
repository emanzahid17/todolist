import streamlit as st
import sqlite3
from datetime import datetime

# Initialize database connection
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

# Create tasks table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        completed BOOLEAN DEFAULT 0,
        deadline TEXT,
        priority TEXT
    )
''')
conn.commit()

# ✅ Add this part here to update columns
cursor.execute("PRAGMA table_info(tasks)")
columns = [col[1] for col in cursor.fetchall()]

if "deadline" not in columns:
    cursor.execute("ALTER TABLE tasks ADD COLUMN deadline TEXT")

if "priority" not in columns:
    cursor.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Medium'")

conn.commit()

# Function to fetch all tasks
def get_tasks():
    cursor.execute("SELECT id, title, completed, deadline, priority FROM tasks ORDER BY completed ASC, priority DESC, deadline ASC")
    return cursor.fetchall()  # Returns a list of (id, title, completed, deadline, priority) tuples


# Function to add a task
def add_task(title, deadline, priority):
    cursor.execute("INSERT INTO tasks (title, completed, deadline, priority) VALUES (?, ?, ?, ?)", (title, False, deadline, priority))
    conn.commit()


# Function to update a task
def update_task(task_id, new_title, new_deadline, new_priority):
    cursor.execute("UPDATE tasks SET title=?, deadline=?, priority=? WHERE id=?", (new_title, new_deadline, new_priority, task_id))
    conn.commit()


# Function to delete a task
def delete_task(task_id):
    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()


# Function to mark a task as complete/incomplete
def mark_completed(task_id, status):
    cursor.execute("UPDATE tasks SET completed=? WHERE id=?", (status, task_id))
    conn.commit()


# Function to count total and completed tasks for progress bar
def count_tasks():
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed=1")
    completed = cursor.fetchone()[0]

    return total, completed


# Streamlit UI Configuration
st.set_page_config(page_title="To-Do List", layout="wide")

st.title("✅ To-Do List App")

# Progress bar below title
total_tasks, completed_tasks = count_tasks()
progress = completed_tasks / total_tasks if total_tasks > 0 else 0
st.progress(progress)
st.write(f"📊 **{completed_tasks}/{total_tasks} tasks completed**")

# Sidebar: Add Task
st.sidebar.header("➕ Add New Task")
with st.sidebar.form(key="new_task_form"):
    task_title = st.text_input("Task Title")
    task_deadline = st.date_input("Deadline", min_value=datetime.today().date())
    task_priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    submit = st.form_submit_button("Add Task")

if submit:
    if task_title.strip():
        add_task(task_title.strip(), str(task_deadline), task_priority)
        st.sidebar.success("Task added successfully!")
        st.rerun()  # ✅ Refresh UI
    else:
        st.sidebar.error("Please enter a task title.")

# Display all tasks
st.subheader("📌 Your Tasks")

tasks = get_tasks()

if not tasks:
    st.info("No tasks found. Add a task from the sidebar!")
else:
    for task in tasks:
        task_id, title, completed, deadline, priority = task  # ✅ FIXED unpacking issue

        col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 1, 1, 1])

        # Task details
        with col1:
            st.write(f"📝 **{title}**")
            st.write(f"📅 Deadline: {deadline}")
            st.write(f"🔥 Priority: {priority}")

        with col2:
            completed_checkbox = st.checkbox("✅ Completed", value=bool(completed), key=f"complete_{task_id}")
            if completed_checkbox != completed:
                mark_completed(task_id, completed_checkbox)
                st.rerun()  # ✅ Refresh UI immediately

        # Edit Button
        with col3:
            if st.button("✏️ Edit", key=f"edit_{task_id}"):
                st.session_state[f"editing_{task_id}"] = True

        # Delete Button
        with col4:
            if st.button("🗑️", key=f"delete_{task_id}"):
                delete_task(task_id)
                st.warning("Task deleted!")
                st.rerun()  # ✅ Refresh UI after delete

        # Edit Mode
        if st.session_state.get(f"editing_{task_id}", False):
            st.subheader("Edit Task")
            with st.form(key=f"edit_form_{task_id}"):
                new_title = st.text_input("Task Title", value=title)
                new_deadline = st.date_input("Deadline", value=datetime.strptime(deadline, "%Y-%m-%d").date())
                new_priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(priority))
                save_changes = st.form_submit_button("Save Changes")

                if save_changes:
                    update_task(task_id, new_title, str(new_deadline), new_priority)
                    st.session_state[f"editing_{task_id}"] = False
                    st.success("Task updated!")
                    st.rerun()  # ✅ Refresh UI after update
