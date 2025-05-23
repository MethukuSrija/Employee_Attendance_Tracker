import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import openpyxl
from collections import defaultdict
from tkcalendar import DateEntry
import os

# --- Configuration and Constants ---
DB_NAME = 'employee_attendance.db'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '1234' # In a real app, hash this!

# Aesthetic and Professional Color Palette
COLOR_PRIMARY = "#85c1e9"  # Indigo (Deep Blue)
COLOR_ACCENT = "#3F51B5"   # Light Indigo
COLOR_BACKGROUND = "#ebdef0" # Very Light Gray (Off-white)
COLOR_TEXT = "#2c3e50"     # Dark Gray
COLOR_BUTTON_TEXT = "#2c3e50" # White
COLOR_WARNING = "#FF9800"  # Orange (for warnings)
COLOR_ERROR = "#D32F2F"    # Dark Red (for errors)
COLOR_HIGHLIGHT = "#BBDEFB" # Light Blue (for selections/hover)


FONT_LARGE = ("Inter", 18, "bold")
FONT_MEDIUM = ("Inter", 16)
FONT_SMALL = ("Inter", 12)

# --- Database Operations ---
def init_db():
    """Initializes the SQLite database and preloads dummy data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            join_date TEXT NOT NULL,
            salary REAL NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date TEXT NOT NULL,
            status TEXT NOT NULL, -- 'Present' or 'Absent'
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

    # Preload dummy employees if table is empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        dummy_employees = [
            ("Alice Smith", "2023-01-15", 50000, "alice123"),
            ("Bob Johnson", "2023-02-20", 60000, "bob456"),
            ("Charlie Brown", "2023-03-10", 45000, "charlie789"),
            ("Diana Prince", "2023-04-01", 70000, "diana000"),
            ("Eve Adams", "2023-05-05", 55000, "eve111"),
            ("Frank White", "2023-06-12", 48000, "frank222"),
            ("Grace Lee", "2023-07-18", 62000, "grace333"),
            ("Henry King", "2023-08-25", 53000, "henry444"),
            ("Ivy Chen", "2023-09-01", 58000, "ivy555"),
            ("Jack Green", "2023-10-10", 65000, "jack666")
        ]
        cursor.executemany("INSERT INTO employees (name, join_date, salary, password) VALUES (?, ?, ?, ?)", dummy_employees)
        conn.commit()

        # Preload some dummy attendance data for the last 30 days
        today = datetime.now().date()
        for i in range(30):
            current_date = today - timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            for emp_id in range(1, 11): # For each dummy employee
                status = 'Present' if (emp_id + i) % 3 != 0 else 'Absent' # Mostly present, some absent
                cursor.execute("INSERT INTO attendance (employee_id, date, status) VALUES (?, ?, ?)",
                               (emp_id, date_str, status))
        conn.commit()

    conn.close()

def get_employees(search_query=""):
    """Fetches all employees from the database, optionally filtered by search_query."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if search_query:
        # Search by name or ID
        cursor.execute("SELECT id, name, join_date, salary FROM employees WHERE name LIKE ? OR CAST(id AS TEXT) LIKE ? ORDER BY name",
                       (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT id, name, join_date, salary FROM employees ORDER BY name")
    employees = cursor.fetchall()
    conn.close()
    return employees

def get_employee_by_id(emp_id):
    """Fetches a single employee by ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, join_date, salary, password FROM employees WHERE id = ?", (emp_id,))
    employee = cursor.fetchone()
    conn.close()
    return employee

def add_employee(name, join_date, salary, password):
    """Adds a new employee to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO employees (name, join_date, salary, password) VALUES (?, ?, ?, ?)",
                       (name, join_date, salary, password))
        conn.commit()
        messagebox.showinfo("Success", f"Employee '{name}' added successfully!")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to add employee: {e}")
    finally:
        conn.close()

def update_employee(emp_id, name, join_date, salary, password):
    """Updates an existing employee's details."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE employees SET name = ?, join_date = ?, salary = ?, password = ? WHERE id = ?",
                       (name, join_date, salary, password, emp_id))
        conn.commit()
        messagebox.showinfo("Success", f"Employee ID {emp_id} updated successfully!")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to update employee: {e}")
    finally:
        conn.close()

def delete_employee(emp_id):
    """Deletes an employee and their attendance records."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Delete attendance records first due to foreign key constraint
        cursor.execute("DELETE FROM attendance WHERE employee_id = ?", (emp_id,))
        cursor.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
        conn.commit()
        messagebox.showinfo("Success", f"Employee ID {emp_id} and their attendance records deleted.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to delete employee: {e}")
    finally:
        conn.close()

def mark_attendance(employee_id, date, status):
    """Marks attendance for a given employee on a specific date. Updates if exists, inserts if new."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Check if attendance already exists for this employee on this date
        cursor.execute("SELECT id FROM attendance WHERE employee_id = ? AND date = ?", (employee_id, date))
        existing_record = cursor.fetchone()

        if existing_record:
            cursor.execute("UPDATE attendance SET status = ? WHERE id = ?", (status, existing_record[0]))
            messagebox.showinfo("Info", f"Attendance for Employee ID {employee_id} on {date} updated to '{status}'.")
        else:
            cursor.execute("INSERT INTO attendance (employee_id, date, status) VALUES (?, ?, ?)",
                           (employee_id, date, status))
            messagebox.showinfo("Success", f"Attendance for Employee ID {employee_id} on {date} marked as '{status}'.")
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to mark attendance: {e}")
    finally:
        conn.close()

def get_attendance_by_employee(employee_id):
    """Fetches all attendance records for a specific employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT date, status FROM attendance WHERE employee_id = ? ORDER BY date DESC", (employee_id,))
    attendance = cursor.fetchall()
    conn.close()
    return attendance

def get_attendance_by_date(date):
    """Fetches attendance records for all employees on a specific date."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.name, a.status
        FROM employees e
        LEFT JOIN attendance a ON e.id = a.employee_id AND a.date = ?
        ORDER BY e.name
    """, (date,))
    attendance = cursor.fetchall()
    conn.close()
    return attendance

def get_monthly_attendance_percentage(employee_id, year, month):
    """Calculates monthly attendance percentage for an employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get total days in the month
    if month == 12:
        next_month_date = datetime(year + 1, 1, 1)
    else:
        next_month_date = datetime(year, month + 1, 1)
    first_day_of_month = datetime(year, month, 1)
    days_in_month = (next_month_date - first_day_of_month).days

    # Count present days
    cursor.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE employee_id = ?
        AND STRFTIME('%Y-%m', date) = ?
        AND status = 'Present'
    """, (employee_id, f"{year:04d}-{month:02d}"))
    present_days = cursor.fetchone()[0]

    conn.close()

    if days_in_month == 0: # Should not happen for valid month/year
        return 0
    return (present_days / days_in_month) * 100

def calculate_salary(employee_id, year, month):
    """Calculates salary based on monthly attendance percentage."""
    employee = get_employee_by_id(employee_id)
    if not employee:
        return 0

    base_salary = employee[3]
    attendance_percentage = get_monthly_attendance_percentage(employee_id, year, month)
    return (base_salary / 100) * attendance_percentage

def get_employees_low_attendance(year, month, threshold=50):
    """Lists employees with attendance percentage below a given threshold."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get total days in the month
    if month == 12:
        next_month_date = datetime(year + 1, 1, 1)
    else:
        next_month_date = datetime(year, month + 1, 1)
    first_day_of_month = datetime(year, month, 1)
    days_in_month = (next_month_date - first_day_of_month).days

    if days_in_month == 0:
        return []

    cursor.execute(f"""
        SELECT e.id, e.name,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_days
        FROM employees e
        LEFT JOIN attendance a ON e.id = a.employee_id
        WHERE STRFTIME('%Y-%m', a.date) = ?
        GROUP BY e.id, e.name
        HAVING (CAST(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS REAL) / {days_in_month}) * 100 < ?
        ORDER BY e.name
    """, (f"{year:04d}-{month:02d}", threshold))
    low_attendance_employees = cursor.fetchall()
    conn.close()
    return low_attendance_employees

def update_employee_password(emp_id, new_password):
    """Updates an employee's password in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE employees SET password = ? WHERE id = ?", (new_password, emp_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error updating password: {e}")
        return False
    finally:
        conn.close()

# --- Main Application Class ---
class EmployeeAttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Attendance System")
        self.root.geometry("1000x700") # Increased size for better layout
        self.root.configure(bg=COLOR_BACKGROUND)

        # Apply a theme to ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'
        self.style.configure('TFrame', background=COLOR_BACKGROUND)
        self.style.configure('TLabel', background=COLOR_BACKGROUND, foreground=COLOR_TEXT, font=FONT_MEDIUM)
        self.style.configure('TButton', background=COLOR_PRIMARY, foreground=COLOR_BUTTON_TEXT, font=FONT_MEDIUM,
                             relief="flat", borderwidth=0, padding=10)
        self.style.map('TButton',
                       background=[('active', COLOR_ACCENT)],
                       foreground=[('active', COLOR_BUTTON_TEXT)])
        self.style.configure('TEntry', fieldbackground="white", foreground=COLOR_TEXT, font=FONT_MEDIUM,
                             relief="solid", borderwidth=1)
        self.style.configure('Treeview', background="white", foreground=COLOR_TEXT, font=FONT_SMALL,
                             fieldbackground="white")
        self.style.configure('Treeview.Heading', font=FONT_MEDIUM, background=COLOR_PRIMARY, foreground=COLOR_BUTTON_TEXT)
        self.style.map('Treeview.Heading', background=[('active', COLOR_ACCENT)])

        # Define a specific style for the chart display frame to give it a background
        self.style.configure('ChartFrame.TFrame', background="#E0F2F7") # Light Blue for visibility

        self.current_user = None
        self.mark_status_var = tk.StringVar(value="Present")
        print("DEBUG: mark_status_var initialized in __init__.") # Stores 'admin' or employee_id

        # Initialize the StringVar here so it's always available
        self.mark_status_var = tk.StringVar(value="Present")

        self.login_frame()

    def clear_frame(self):
        """Clears all widgets from the current frame."""
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- Login Screen ---
    def login_frame(self):
        self.clear_frame()

        self.root.configure(bg=COLOR_BACKGROUND) # Ensure background color is set

        login_frame = ttk.Frame(self.root, padding="30 30 30 30", relief="solid", borderwidth=1, style='TFrame')
        login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(login_frame, text="Login", font=FONT_LARGE).grid(row=0, column=0, columnspan=2, pady=20)

        ttk.Label(login_frame, text="Username/Employee ID:").grid(row=1, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=1, column=1, pady=5)

        ttk.Label(login_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, pady=5)

        ttk.Button(login_frame, text="Admin Login", command=self.admin_login).grid(row=3, column=0, pady=10, padx=5, sticky="ew")
        ttk.Button(login_frame, text="Employee Login", command=self.employee_login).grid(row=3, column=1, pady=10, padx=5, sticky="ew")

        # Center the login frame
        login_frame.grid_rowconfigure(0, weight=1)
        login_frame.grid_rowconfigure(4, weight=1)
        login_frame.grid_columnconfigure(0, weight=1)
        login_frame.grid_columnconfigure(1, weight=1)

    def admin_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            self.current_user = 'admin'
            messagebox.showinfo("Login Success", "Welcome, Admin!")
            self.admin_panel()
        else:
            messagebox.showerror("Login Failed", "Invalid Admin Credentials")

    def employee_login(self):
        emp_id_str = self.username_entry.get()
        password = self.password_entry.get()

        try:
            emp_id = int(emp_id_str)
            employee = get_employee_by_id(emp_id)

            if employee and employee[4] == password: # employee[4] is the password field
                self.current_user = emp_id
                messagebox.showinfo("Login Success", f"Welcome, {employee[1]}!")
                self.employee_panel()
            else:
                messagebox.showerror("Login Failed", "Invalid Employee ID or Password")
        except ValueError:
            messagebox.showerror("Input Error", "Employee ID must be a number.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # --- Admin Panel ---
    def admin_panel(self):
        self.clear_frame()
        self.root.unbind("<Configure>")

        admin_frame = ttk.Frame(self.root, padding="20", style='TFrame')
        admin_frame.pack(fill="both", expand=True)

        # Header with Logout Button
        header_frame = ttk.Frame(admin_frame, style='TFrame')
        header_frame.pack(fill="x", pady=10)
        ttk.Label(header_frame, text="Admin Dashboard", font=FONT_LARGE).pack(side="left", padx=10)
        ttk.Button(header_frame, text="Logout", command=self.logout).pack(side="right", padx=10)

        # Notebook for different sections
        self.admin_notebook = ttk.Notebook(admin_frame)
        self.admin_notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Employee Management Tab
        self.employee_tab = ttk.Frame(self.admin_notebook, style='TFrame')
        self.admin_notebook.add(self.employee_tab, text="Employee Management")
        self.setup_employee_management_tab(self.employee_tab)

        # Attendance Management Tab
        self.attendance_tab = ttk.Frame(self.admin_notebook, style='TFrame')
        self.admin_notebook.add(self.attendance_tab, text="Attendance Management")
        self.setup_attendance_management_tab(self.attendance_tab)

        # Reports & Charts Tab (THIS IS THE KEY PART)
        self.reports_tab = ttk.Frame(self.admin_notebook, style='TFrame')
        self.admin_notebook.add(self.reports_tab, text="Reports & Charts") # Ensure this line is present
        self.setup_reports_charts_tab(self.reports_tab) # Ensure this function call is present

    def logout(self):
        self.current_user = None
        messagebox.showinfo("Logged Out", "You have been logged out.")
        self.login_frame()

    # --- Employee Management Tab ---
    def setup_employee_management_tab(self, parent_frame):
        # Left side: Form for Add/Update
        form_frame = ttk.LabelFrame(parent_frame, text="Employee Details", padding="15", style='TFrame')
        form_frame.pack(side="left", fill="y", padx=10, pady=10)

        labels = ["ID (for update):", "Name:", "Join Date:", "Salary:", "Password:"]
        self.emp_entries = {}
        for i, text in enumerate(labels):
            ttk.Label(form_frame, text=text).grid(row=i, column=0, sticky="w", pady=5)
            if "Join Date" in text:
                date_entry = DateEntry(form_frame, width=27, background=COLOR_PRIMARY,
                                       foreground='white', borderwidth=2, year=datetime.now().year,
                                       month=datetime.now().month, day=datetime.now().day,
                                       date_pattern='yyyy-mm-dd')
                date_entry.grid(row=i, column=1, pady=5)
                self.emp_entries[text.split(':')[0].strip()] = date_entry
            else:
                entry = ttk.Entry(form_frame, width=30)
                entry.grid(row=i, column=1, pady=5)
                self.emp_entries[text.split(':')[0].strip()] = entry

        # Buttons for actions
        button_frame = ttk.Frame(form_frame, style='TFrame')
        button_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Add Employee", command=self.add_employee_action).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Update Employee", command=self.update_employee_action).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_employee_form).pack(side="left", padx=5)

        # Right side: Employee List with Search
        list_frame = ttk.LabelFrame(parent_frame, text="All Employees", padding="15", style='TFrame')
        list_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Search bar
        search_frame = ttk.Frame(list_frame, style='TFrame')
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_employees)
        ttk.Button(search_frame, text="Clear Search", command=self.clear_search).pack(side="left", padx=5)


        self.employee_tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Join Date", "Salary"), show="headings")
        self.employee_tree.heading("ID", text="ID")
        self.employee_tree.heading("Name", text="Name")
        self.employee_tree.heading("Join Date", text="Join Date")
        self.employee_tree.heading("Salary", text="Salary")

        self.employee_tree.column("ID", width=50, anchor="center")
        self.employee_tree.column("Name", width=150)
        self.employee_tree.column("Join Date", width=100, anchor="center")
        self.employee_tree.column("Salary", width=100, anchor="e")

        self.employee_tree.pack(fill="both", expand=True)

        # Scrollbar for the Treeview
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.employee_tree.yview)
        self.employee_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Buttons for Treeview actions
        tree_button_frame = ttk.Frame(list_frame, style='TFrame')
        tree_button_frame.pack(pady=10)
        ttk.Button(tree_button_frame, text="View Details", command=self.view_employee_details).pack(side="left", padx=5)
        ttk.Button(tree_button_frame, text="Delete Employee", command=self.delete_employee_action).pack(side="left", padx=5)
        ttk.Button(tree_button_frame, text="Refresh List", command=self.load_employees_to_tree).pack(side="left", padx=5)

        self.employee_tree.bind("<<TreeviewSelect>>", self.on_employee_select)
        self.load_employees_to_tree()

    def load_employees_to_tree(self, search_query=""):
        """Loads all employees into the Treeview, optionally filtered by search_query."""
        for i in self.employee_tree.get_children():
            self.employee_tree.delete(i)
        employees = get_employees(search_query)
        for emp in employees:
            self.employee_tree.insert("", "end", values=emp)

    def filter_employees(self, event=None):
        """Filters the employee list based on the search entry."""
        search_query = self.search_entry.get()
        self.load_employees_to_tree(search_query)

    def clear_search(self):
        """Clears the search bar and reloads all employees."""
        self.search_entry.delete(0, tk.END)
        self.load_employees_to_tree()

    def clear_employee_form(self):
        """Clears all entry fields in the employee form."""
        for key, entry in self.emp_entries.items():
            if isinstance(entry, DateEntry):
                entry.set_date(datetime.now().date()) # Reset DateEntry to today
            else:
                entry.delete(0, tk.END)

    def add_employee_action(self):
        name = self.emp_entries["Name"].get()
        join_date = self.emp_entries["Join Date"].get_date().strftime('%Y-%m-%d') # Get date from DateEntry
        salary_str = self.emp_entries["Salary"].get()
        password = self.emp_entries["Password"].get()

        if not all([name, join_date, salary_str, password]):
            messagebox.showerror("Input Error", "All fields except 'ID' are required for adding an employee.")
            return

        try:
            salary = float(salary_str)
        except ValueError:
            messagebox.showerror("Input Error", "Salary must be a number.")
            return

        add_employee(name, join_date, salary, password)
        self.load_employees_to_tree()
        self.clear_employee_form()

    def update_employee_action(self):
        emp_id_str = self.emp_entries["ID (for update)"].get()
        name = self.emp_entries["Name"].get()
        join_date = self.emp_entries["Join Date"].get_date().strftime('%Y-%m-%d') # Get date from DateEntry
        salary_str = self.emp_entries["Salary"].get()
        password = self.emp_entries["Password"].get()

        if not emp_id_str:
            messagebox.showerror("Input Error", "Employee ID is required for updating.")
            return
        if not all([name, join_date, salary_str, password]):
            messagebox.showerror("Input Error", "All fields are required for updating an employee.")
            return

        try:
            emp_id = int(emp_id_str)
            salary = float(salary_str)
        except ValueError:
            messagebox.showerror("Input Error", "ID and Salary must be numbers.")
            return

        update_employee(emp_id, name, join_date, salary, password)
        self.load_employees_to_tree()
        self.clear_employee_form()

    def delete_employee_action(self):
        selected_item = self.employee_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an employee to delete.")
            return

        emp_id = self.employee_tree.item(selected_item, 'values')[0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Employee ID {emp_id}? This will also delete all their attendance records."):
            delete_employee(emp_id)
            self.load_employees_to_tree()
            self.clear_employee_form()

    def on_employee_select(self, event):
        """Populates the form when an employee is selected in the Treeview."""
        selected_item = self.employee_tree.selection()
        if selected_item:
            values = self.employee_tree.item(selected_item, 'values')
            emp_id = values[0]
            employee_details = get_employee_by_id(emp_id) # Fetch full details including password

            if employee_details:
                self.clear_employee_form()
                self.emp_entries["ID (for update)"].insert(0, employee_details[0])
                self.emp_entries["Name"].insert(0, employee_details[1])
                # Set DateEntry value
                try:
                    join_date_dt = datetime.strptime(employee_details[2], '%Y-%m-%d').date()
                    self.emp_entries["Join Date"].set_date(join_date_dt)
                except ValueError:
                    self.emp_entries["Join Date"].set_date(datetime.now().date()) # Fallback
                self.emp_entries["Salary"].insert(0, employee_details[3])
                self.emp_entries["Password"].insert(0, employee_details[4]) # Populate password field

    def view_employee_details(self):
        selected_item = self.employee_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an employee to view details.")
            return

        emp_id = self.employee_tree.item(selected_item, 'values')[0]
        employee = get_employee_by_id(emp_id)
        if employee:
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Details for {employee[1]}")
            details_window.geometry("400x300")
            details_window.transient(self.root) # Make it appear on top of main window
            details_window.grab_set() # Disable interaction with main window

            ttk.Label(details_window, text=f"Employee ID: {employee[0]}", font=FONT_MEDIUM).pack(pady=5)
            ttk.Label(details_window, text=f"Name: {employee[1]}", font=FONT_MEDIUM).pack(pady=5)
            ttk.Label(details_window, text=f"Join Date: {employee[2]}", font=FONT_MEDIUM).pack(pady=5)
            ttk.Label(details_window, text=f"Salary: {employee[3]:,.2f}", font=FONT_MEDIUM).pack(pady=5)

            ttk.Label(details_window, text="\nAttendance History:", font=FONT_MEDIUM).pack(pady=5)
            attendance_history = get_attendance_by_employee(emp_id)
            if attendance_history:
                history_text = "\n".join([f"{date}: {status}" for date, status in attendance_history[:10]]) # Show last 10
                if len(attendance_history) > 10:
                    history_text += "\n..."
                ttk.Label(details_window, text=history_text, font=FONT_SMALL).pack(pady=5)
            else:
                ttk.Label(details_window, text="No attendance records found.", font=FONT_SMALL).pack(pady=5)

            ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)

    # --- Attendance Management Tab (Admin) ---
    def setup_attendance_management_tab(self, parent_frame):
        # Top: Mark/Edit Attendance Section
        mark_edit_frame = ttk.LabelFrame(parent_frame, text="Mark/Edit Daily Attendance", padding="15", style='TFrame')
        mark_edit_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(mark_edit_frame, text="Employee ID:").grid(row=0, column=0, sticky="w", pady=5)
        self.mark_emp_id_entry = ttk.Entry(mark_edit_frame, width=15)
        self.mark_emp_id_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(mark_edit_frame, text="Date:").grid(row=0, column=2, sticky="w", pady=5)
        self.mark_date_entry = DateEntry(mark_edit_frame, width=12, background=COLOR_PRIMARY,
                                         foreground='white', borderwidth=2, year=datetime.now().year,
                                         month=datetime.now().month, day=datetime.now().day,
                                         date_pattern='yyyy-mm-dd')
        self.mark_date_entry.grid(row=0, column=3, pady=5, padx=5)

        ttk.Label(mark_edit_frame, text="Status:").grid(row=0, column=4, sticky="w", pady=5)
        # self.mark_status_var = tk.StringVar(value="Present") # MOVED TO __init__
        ttk.Radiobutton(mark_edit_frame, text="Present", variable=self.mark_status_var, value="Present").grid(row=0, column=5, padx=5)
        ttk.Radiobutton(mark_edit_frame, text="Absent", variable=self.mark_status_var, value="Absent").grid(row=0, column=6, padx=5)

        ttk.Button(mark_edit_frame, text="Mark/Update Attendance", command=self.mark_attendance_action_admin).grid(row=0, column=7, padx=10, sticky="ew")

        # Middle: View Attendance by Date
        view_by_date_frame = ttk.LabelFrame(parent_frame, text="View Attendance by Date", padding="15", style='TFrame')
        view_by_date_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(view_by_date_frame, text="Date:").grid(row=0, column=0, sticky="w", pady=5)
        self.view_date_entry = DateEntry(view_by_date_frame, width=12, background=COLOR_PRIMARY,
                                        foreground='white', borderwidth=2, year=datetime.now().year,
                                        month=datetime.now().month, day=datetime.now().day,
                                        date_pattern='yyyy-mm-dd')
        self.view_date_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Button(view_by_date_frame, text="Show Attendance", command=self.show_attendance_by_date).grid(row=0, column=2, padx=10, sticky="ew")

        self.attendance_by_date_tree = ttk.Treeview(view_by_date_frame, columns=("ID", "Name", "Status"), show="headings")
        self.attendance_by_date_tree.heading("ID", text="ID")
        self.attendance_by_date_tree.heading("Name", text="Name")
        self.attendance_by_date_tree.heading("Status", text="Status")
        self.attendance_by_date_tree.column("ID", width=50, anchor="center")
        self.attendance_by_date_tree.column("Name", width=150)
        self.attendance_by_date_tree.column("Status", width=100, anchor="center")
        self.attendance_by_date_tree.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=10)
        view_by_date_frame.grid_rowconfigure(1, weight=1)
        view_by_date_frame.grid_columnconfigure(0, weight=1)
        view_by_date_frame.grid_columnconfigure(1, weight=1)
        view_by_date_frame.grid_columnconfigure(2, weight=1)

        # Bottom: Monthly Attendance & Salary Calculation
        monthly_frame = ttk.LabelFrame(parent_frame, text="Monthly Overview", padding="15", style='TFrame')
        monthly_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(monthly_frame, text="Year:").grid(row=0, column=0, sticky="w", pady=5)
        self.monthly_year_entry = ttk.Entry(monthly_frame, width=10)
        self.monthly_year_entry.grid(row=0, column=1, pady=5, padx=5)
        self.monthly_year_entry.insert(0, str(datetime.now().year))

        ttk.Label(monthly_frame, text="Month (1-12):").grid(row=0, column=2, sticky="w", pady=5)
        self.monthly_month_entry = ttk.Entry(monthly_frame, width=10)
        self.monthly_month_entry.grid(row=0, column=3, pady=5, padx=5)
        self.monthly_month_entry.insert(0, str(datetime.now().month))

        ttk.Button(monthly_frame, text="Calculate Monthly Stats", command=self.calculate_monthly_stats).grid(row=0, column=4, padx=10, sticky="ew")
        ttk.Button(monthly_frame, text="Low Attendance (<50%)", command=self.show_low_attendance).grid(row=0, column=5, padx=10, sticky="ew")

        self.monthly_stats_tree = ttk.Treeview(monthly_frame, columns=("ID", "Name", "Present Days", "Percentage", "Calculated Salary"), show="headings")
        self.monthly_stats_tree.heading("ID", text="ID")
        self.monthly_stats_tree.heading("Name", text="Name")
        self.monthly_stats_tree.heading("Present Days", text="Present Days")
        self.monthly_stats_tree.heading("Percentage", text="Percentage (%)")
        self.monthly_stats_tree.heading("Calculated Salary", text="Calculated Salary")

        self.monthly_stats_tree.column("ID", width=50, anchor="center")
        self.monthly_stats_tree.column("Name", width=150)
        self.monthly_stats_tree.column("Present Days", width=100, anchor="center")
        self.monthly_stats_tree.column("Percentage", width=100, anchor="e")
        self.monthly_stats_tree.column("Calculated Salary", width=120, anchor="e")

        # FIX: Changed from .pack() to .grid() to resolve layout manager conflict
        self.monthly_stats_tree.grid(row=1, column=0, columnspan=6, sticky="nsew", pady=10) # Spanning all 6 columns

        # Configure grid weights for expandability
        monthly_frame.grid_rowconfigure(1, weight=1)
        for i in range(6): # For columns 0 to 5
            monthly_frame.grid_columnconfigure(i, weight=1)

    def mark_attendance_action_admin(self):
        """Action specifically for admin to mark/edit attendance."""
        emp_id_str = self.mark_emp_id_entry.get()
        date = self.mark_date_entry.get_date().strftime('%Y-%m-%d')
        status = self.mark_status_var.get()

        if not all([emp_id_str, date, status]):
            messagebox.showerror("Input Error", "All fields are required to mark attendance.")
            return

        try:
            emp_id = int(emp_id_str)
            mark_attendance(emp_id, date, status)
        except ValueError:
            messagebox.showerror("Input Error", "Employee ID must be a number.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")


    def show_attendance_by_date(self):
        date = self.view_date_entry.get_date().strftime('%Y-%m-%d') # Get date from DateEntry
        if not date:
            messagebox.showerror("Input Error", "Please enter a date.")
            return

        for i in self.attendance_by_date_tree.get_children():
            self.attendance_by_date_tree.delete(i)

        attendance_records = get_attendance_by_date(date)
        if not attendance_records:
            messagebox.showinfo("No Records", f"No attendance records found for {date}.")
            return

        for record in attendance_records:
            emp_id, emp_name, status = record
            # If status is None (no record for that date), assume Absent or 'N/A'
            display_status = status if status else "Absent (No Record)"
            self.attendance_by_date_tree.insert("", "end", values=(emp_id, emp_name, display_status))

    def calculate_monthly_stats(self):
        year_str = self.monthly_year_entry.get()
        month_str = self.monthly_month_entry.get()

        if not all([year_str, month_str]):
            messagebox.showerror("Input Error", "Please enter year and month.")
            return

        try:
            year = int(year_str)
            month = int(month_str)
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid year or month: {e}")
            return

        for i in self.monthly_stats_tree.get_children():
            self.monthly_stats_tree.delete(i)

        employees = get_employees()
        for emp_id, name, _, _ in employees:
            attendance_percentage = get_monthly_attendance_percentage(emp_id, year, month)
            calculated_salary = calculate_salary(emp_id, year, month)

            # Get present days for display
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM attendance
                WHERE employee_id = ?
                AND STRFTIME('%Y-%m', date) = ?
                AND status = 'Present'
            """, (emp_id, f"{year:04d}-{month:02d}"))
            present_days = cursor.fetchone()[0]
            conn.close()

            self.monthly_stats_tree.insert("", "end", values=(emp_id, name, present_days, f"{attendance_percentage:.2f}", f"{calculated_salary:,.2f}"))

    def show_low_attendance(self):
        year_str = self.monthly_year_entry.get()
        month_str = self.monthly_month_entry.get()

        if not all([year_str, month_str]):
            messagebox.showerror("Input Error", "Please enter year and month for low attendance check.")
            return

        try:
            year = int(year_str)
            month = int(month_str)
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid year or month: {e}")
            return

        low_attendance_employees = get_employees_low_attendance(year, month, threshold=50)

        if not low_attendance_employees:
            messagebox.showinfo("No Low Attendance", f"No employees found with less than 50% attendance for {month}/{year}.")
            return

        low_attendance_text = f"Employees with <50% attendance for {month}/{year}:\n\n"
        for emp_id, name, present_days in low_attendance_employees:
            # Recalculate percentage for display as get_employees_low_attendance returns present_days
            if month == 12:
                next_month_date = datetime(year + 1, 1, 1)
            else:
                next_month_date = datetime(year, month + 1, 1)
            first_day_of_month = datetime(year, month, 1)
            days_in_month = (next_month_date - first_day_of_month).days
            percentage = (present_days / days_in_month) * 100 if days_in_month > 0 else 0
            low_attendance_text += f"ID: {emp_id}, Name: {name}, Present Days: {present_days}, Percentage: {percentage:.2f}%\n"

        messagebox.showwarning("Low Attendance Alert", low_attendance_text)

    # --- Reports & Charts Tab ---
    def setup_reports_charts_tab(self, parent_frame):
        # Frame for controls
        control_frame = ttk.Frame(parent_frame, style='TFrame')
        control_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(control_frame, text="Employee ID (for single employee chart):").grid(row=0, column=0, sticky="w", pady=5)
        self.chart_emp_id_entry = ttk.Entry(control_frame, width=15)
        self.chart_emp_id_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(control_frame, text="Year:").grid(row=0, column=2, sticky="w", pady=5)
        self.chart_year_entry = ttk.Entry(control_frame, width=10)
        self.chart_year_entry.grid(row=0, column=3, pady=5, padx=5)
        self.chart_year_entry.insert(0, str(datetime.now().year))

        ttk.Label(control_frame, text="Month (1-12):").grid(row=0, column=4, sticky="w", pady=5)
        self.chart_month_entry = ttk.Entry(control_frame, width=10)
        self.chart_month_entry.grid(row=0, column=5, pady=5, padx=5)
        self.chart_month_entry.insert(0, str(datetime.now().month))

        ttk.Button(control_frame, text="Generate Employee Chart", command=self.generate_employee_chart).grid(row=1, column=0, columnspan=2, pady=10, padx=5, sticky="ew")
        ttk.Button(control_frame, text="Generate Monthly Bar Chart (All)", command=self.generate_all_employees_bar_chart).grid(row=1, column=2, columnspan=3, pady=10, padx=5, sticky="ew")
        ttk.Button(control_frame, text="Export All Attendance to Excel", command=self.export_all_attendance_to_excel).grid(row=1, column=5, columnspan=2, pady=10, padx=5, sticky="ew")

        # Frame for charts - Using the custom style 'ChartFrame.TFrame' for background
        self.chart_display_frame = ttk.Frame(parent_frame, style='ChartFrame.TFrame', relief="solid", borderwidth=2)
        self.chart_display_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def generate_employee_chart(self):
        emp_id_str = self.chart_emp_id_entry.get()
        year_str = self.chart_year_entry.get()
        month_str = self.chart_month_entry.get()

        if not all([emp_id_str, year_str, month_str]):
            messagebox.showerror("Input Error", "Employee ID, Year, and Month are required for the chart.")
            return

        try:
            emp_id = int(emp_id_str)
            year = int(year_str)
            month = int(month_str)
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return

        employee = get_employee_by_id(emp_id)
        if not employee:
            messagebox.showerror("Error", f"Employee with ID {emp_id} not found.")
            return

        # Get total days in the month
        if month == 12:
            next_month_date = datetime(year + 1, 1, 1)
        else:
            next_month_date = datetime(year, month + 1, 1)
        first_day_of_month = datetime(year, month, 1)
        days_in_month = (next_month_date - first_day_of_month).days

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) FROM attendance
            WHERE employee_id = ?
            AND STRFTIME('%Y-%m', date) = ?
            GROUP BY status
        """, (emp_id, f"{year:04d}-{month:02d}"))
        attendance_counts = dict(cursor.fetchall())
        conn.close()

        present_days = attendance_counts.get('Present', 0)
        absent_days = attendance_counts.get('Absent', 0)
        unmarked_days = days_in_month - (present_days + absent_days)
        if unmarked_days < 0: unmarked_days = 0 # Handle cases where data might be inconsistent (e.g., future dates)

        # --- DEBUGGING PRINTS ---
        print(f"--- Chart Data for Employee ID {emp_id} ({month}/{year}) ---")
        print(f"Days in month: {days_in_month}")
        print(f"Attendance counts from DB: {attendance_counts}")
        print(f"Present days: {present_days}")
        print(f"Absent days: {absent_days}")
        print(f"Unmarked days: {unmarked_days}")
        # --- END DEBUGGING PRINTS ---

        labels = ['Present', 'Absent', 'Unmarked']
        sizes = [present_days, absent_days, unmarked_days]
        colors = [COLOR_PRIMARY, COLOR_ERROR, COLOR_WARNING]
        explode = (0.1, 0, 0) # explode the 'Present' slice

        # Filter out labels/sizes for zero values. If all are zero, Matplotlib might not draw.
        # This also prevents drawing slices for categories with 0 data.
        filtered_data = [(l, s, c, e) for l, s, c, e in zip(labels, sizes, colors, explode) if s > 0]
        if not filtered_data:
            messagebox.showinfo("No Data", f"No attendance data found for Employee ID {emp_id} in {month}/{year} to generate a chart.")
            # Clear any previous chart if no data is found
            for widget in self.chart_display_frame.winfo_children():
                widget.destroy()
            return

        labels, sizes, colors, explode = zip(*filtered_data)


        # Clear previous chart
        for widget in self.chart_display_frame.winfo_children():
            widget.destroy()

        # Create the figure and axes
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=90)
        ax.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title(f"Attendance for {employee[1]} ({month}/{year})")

        # Embed the matplotlib figure into Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_display_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True) # Ensure it expands to fill the frame
        canvas.draw() # Explicitly draw the canvas

        # Close the matplotlib figure to free memory (important in loops/repeated calls)
        plt.close(fig)


    def generate_all_employees_bar_chart(self):
        year_str = self.chart_year_entry.get()
        month_str = self.chart_month_entry.get()

        if not all([year_str, month_str]):
            messagebox.showerror("Input Error", "Year and Month are required for the chart.")
            return

        try:
            year = int(year_str)
            month = int(month_str)
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return

        employees = get_employees()
        employee_names = [emp[1] for emp in employees]
        attendance_percentages = []

        for emp_id, _, _, _ in employees:
            percentage = get_monthly_attendance_percentage(emp_id, year, month)
            attendance_percentages.append(percentage)

        # --- DEBUGGING PRINTS ---
        print(f"--- Bar Chart Data for All Employees ({month}/{year}) ---")
        print(f"Employee Names: {employee_names}")
        print(f"Attendance Percentages: {attendance_percentages}")
        # --- END DEBUGGING PRINTS ---

        # Clear previous chart
        for widget in self.chart_display_frame.winfo_children():
            widget.destroy()

        # Check if there's any data to plot
        if not employee_names or all(p == 0 for p in attendance_percentages):
            messagebox.showinfo("No Data", f"No attendance data found for any employee in {month}/{year} to generate a bar chart.")
            return


        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(employee_names, attendance_percentages, color=COLOR_PRIMARY)
        ax.set_ylabel('Attendance Percentage (%)')
        ax.set_title(f'Monthly Attendance Percentage for All Employees ({month}/{year})')
        ax.set_ylim(0, 100)
        plt.xticks(rotation=45, ha='right') # Rotate labels for better readability
        plt.tight_layout()

        # Add percentage labels on top of bars
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.1f}%', ha='center', va='bottom', fontsize=8)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_display_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig) # Close the figure

    def export_all_attendance_to_excel(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                      filetypes=[("Excel files", "*.xlsx")],
                                                      title="Save Attendance Data")

            print(f"--- DEBUG: File dialog returned path: '{file_path}' ---")

            if not file_path:
                print("--- DEBUG: File save dialog was cancelled or no path selected. ---")
                messagebox.showinfo("Export Cancelled", "File export was cancelled.")
                return

            # Add more robust path validation
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                print(f"--- ERROR: Directory does not exist: {directory} ---")
                messagebox.showerror("Export Error", f"The selected directory does not exist:\n{directory}")
                return

            if not os.access(directory, os.W_OK):
                print(f"--- ERROR: No write permissions for directory: {directory} ---")
                messagebox.showerror("Permission Denied", f"No write permissions for the selected directory:\n'{directory}'.\nPlease choose a different location or run the application as administrator.")
                return

            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Attendance Data"

            # Header row
            sheet.append(["Employee ID", "Employee Name", "Date", "Status"])

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.name, a.date, a.status
                FROM employees e
                JOIN attendance a ON e.id = a.employee_id
                ORDER BY e.name, a.date
            """)
            all_attendance = cursor.fetchall()
            conn.close()

            print(f"--- DEBUG: Fetched {len(all_attendance)} attendance records from DB. ---")

            if not all_attendance:
                messagebox.showinfo("No Data to Export", "No attendance records found in the database to export.")
                print("--- DEBUG: No attendance data found for export. ---")
                return

            for record in all_attendance:
                sheet.append(record)

            workbook.save(file_path)
            print(f"--- DEBUG: Workbook successfully saved to '{file_path}' ---")

            messagebox.showinfo("Export Success", f"Attendance data exported to:\n{file_path}")

        except PermissionError as pe:
            print(f"--- ERROR: Permission denied during save: {pe} ---")
            messagebox.showerror("Permission Denied", f"Permission denied when saving file:\n'{file_path}'.\nPlease choose a different location or run the application as administrator.")
        except openpyxl.utils.exceptions.InvalidFileException as ife: # Catch specific openpyxl errors
            print(f"--- ERROR: openpyxl Invalid File Exception: {ife} ---")
            messagebox.showerror("Export Error", f"Invalid file error during export. Is the file already open or corrupted?\nError: {ife}")
        except Exception as e:
            print(f"--- CRITICAL ERROR: Unexpected error during export: {e} ---")
            messagebox.showerror("Export Error", f"An unexpected error occurred during export:\n{e}\nPlease check the terminal for more details.")


    # --- Employee Panel ---
    def employee_panel(self):
        self.clear_frame()
        self.root.unbind("<Configure>") # Still good to unbind if it was previously bound by mistake or older version

        employee_frame = ttk.Frame(self.root, padding="20", style='TFrame')
        employee_frame.pack(fill="both", expand=True)

        # Header with Logout Button
        header_frame = ttk.Frame(employee_frame, style='TFrame')
        header_frame.pack(fill="x", pady=10)
        ttk.Label(header_frame, text="Employee Dashboard", font=FONT_LARGE).pack(side="left", padx=10)
        ttk.Button(header_frame, text="Logout", command=self.logout).pack(side="right", padx=10)

        # Notebook for employee sections
        self.employee_notebook = ttk.Notebook(employee_frame)
        self.employee_notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Details Tab
        self.emp_details_tab = ttk.Frame(self.employee_notebook, style='TFrame')
        self.employee_notebook.add(self.emp_details_tab, text="Your Details")
        self.setup_employee_details_tab(self.emp_details_tab)

        # Attendance Tab
        self.emp_attendance_tab = ttk.Frame(self.employee_notebook, style='TFrame')
        self.employee_notebook.add(self.emp_attendance_tab, text="Your Attendance")
        self.setup_employee_attendance_tab(self.emp_attendance_tab)

        # NEW: Mark Your Attendance Tab for employees
        self.emp_mark_attendance_tab = ttk.Frame(self.employee_notebook, style='TFrame')
        self.employee_notebook.add(self.emp_mark_attendance_tab, text="Mark Your Attendance")
        self.setup_employee_mark_attendance_tab(self.emp_mark_attendance_tab)

        # Password Change Tab
        self.emp_password_tab = ttk.Frame(self.employee_notebook, style='TFrame')
        self.employee_notebook.add(self.emp_password_tab, text="Change Password")
        self.setup_employee_password_tab(self.emp_password_tab)


    def setup_employee_details_tab(self, parent_frame):
        emp_details_frame = ttk.LabelFrame(parent_frame, text="Your Personal Information", padding="15", style='TFrame')
        emp_details_frame.pack(fill="x", padx=10, pady=10)

        employee_data = get_employee_by_id(self.current_user)
        if employee_data:
            ttk.Label(emp_details_frame, text=f"Employee ID: {employee_data[0]}", font=FONT_MEDIUM).pack(anchor="w", pady=2)
            ttk.Label(emp_details_frame, text=f"Name: {employee_data[1]}", font=FONT_MEDIUM).pack(anchor="w", pady=2)
            ttk.Label(emp_details_frame, text=f"Join Date: {employee_data[2]}", font=FONT_MEDIUM).pack(anchor="w", pady=2)
            ttk.Label(emp_details_frame, text=f"Salary: {employee_data[3]:,.2f}", font=FONT_MEDIUM).pack(anchor="w", pady=2)
        else:
            ttk.Label(emp_details_frame, text="Could not load employee details.", font=FONT_MEDIUM, foreground=COLOR_ERROR).pack(anchor="w", pady=2)

    def setup_employee_attendance_tab(self, parent_frame):
        # Your Attendance History
        attendance_history_frame = ttk.LabelFrame(parent_frame, text="Your Daily Attendance History", padding="15", style='TFrame')
        attendance_history_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.employee_attendance_tree = ttk.Treeview(attendance_history_frame, columns=("Date", "Status"), show="headings")
        self.employee_attendance_tree.heading("Date", text="Date")
        self.employee_attendance_tree.heading("Status", text="Status")
        self.employee_attendance_tree.column("Date", width=150, anchor="center")
        self.employee_attendance_tree.column("Status", width=100, anchor="center")
        self.employee_attendance_tree.pack(fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(attendance_history_frame, orient="vertical", command=self.employee_attendance_tree.yview)
        self.employee_attendance_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.load_employee_attendance_history()

        # Monthly Attendance Summary
        monthly_summary_frame = ttk.LabelFrame(parent_frame, text="Your Monthly Attendance Summary", padding="15", style='TFrame')
        monthly_summary_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(monthly_summary_frame, text="Year:").grid(row=0, column=0, sticky="w", pady=5)
        self.emp_summary_year_entry = ttk.Entry(monthly_summary_frame, width=10)
        self.emp_summary_year_entry.grid(row=0, column=1, pady=5, padx=5)
        self.emp_summary_year_entry.insert(0, str(datetime.now().year))

        ttk.Label(monthly_summary_frame, text="Month (1-12):").grid(row=0, column=2, sticky="w", pady=5)
        self.emp_summary_month_entry = ttk.Entry(monthly_summary_frame, width=10)
        self.emp_summary_month_entry.grid(row=0, column=3, pady=5, padx=5)
        self.emp_summary_month_entry.insert(0, str(datetime.now().month))

        ttk.Button(monthly_summary_frame, text="Show Summary", command=self.show_employee_monthly_summary).grid(row=0, column=4, padx=10, sticky="ew")

        self.emp_summary_label = ttk.Label(monthly_summary_frame, text="", font=FONT_MEDIUM, wraplength=400)
        self.emp_summary_label.grid(row=1, column=0, columnspan=5, pady=10, sticky="w")

    # NEW: Employee's own attendance marking tab
    def setup_employee_mark_attendance_tab(self, parent_frame):
        print(f"DEBUG: Setting up employee mark attendance tab. self.mark_status_var exists: {hasattr(self, 'mark_status_var')}")
        mark_frame = ttk.LabelFrame(parent_frame, text="Mark Your Daily Attendance", padding="20", style='TFrame')
        mark_frame.pack(fill="x", padx=10, pady=10)

        # Employee ID (pre-filled and read-only)
        ttk.Label(mark_frame, text="Your Employee ID:").grid(row=0, column=0, sticky="w", pady=5)
        self.emp_self_mark_id_entry = ttk.Entry(mark_frame, width=15)
        self.emp_self_mark_id_entry.grid(row=0, column=1, pady=5, padx=5)
        self.emp_self_mark_id_entry.insert(0, str(self.current_user)) # Pre-fill with current user's ID
        self.emp_self_mark_id_entry.config(state='readonly') # Make it read-only

        # Date for attendance
        ttk.Label(mark_frame, text="Date:").grid(row=1, column=0, sticky="w", pady=5)
        self.emp_self_mark_date_entry = DateEntry(mark_frame, width=12, background=COLOR_PRIMARY,
                                                  foreground='white', borderwidth=2,
                                                  year=datetime.now().year,
                                                  month=datetime.now().month,
                                                  day=datetime.now().day,
                                                  date_pattern='yyyy-mm-dd')
        self.emp_self_mark_date_entry.grid(row=1, column=1, pady=5, padx=5)

        # Status (Present/Absent)
        ttk.Label(mark_frame, text="Status:").grid(row=2, column=0, sticky="w", pady=5)
        # Use the same self.mark_status_var as admin, as it's just a StringVar shared across the instance
        # This will simplify the mark_attendance_action.
        self.mark_status_var.set("Present") # Ensure default is Present for this tab
        ttk.Radiobutton(mark_frame, text="Present", variable=self.mark_status_var, value="Present").grid(row=2, column=1, padx=5, sticky="w")
        ttk.Radiobutton(mark_frame, text="Absent", variable=self.mark_status_var, value="Absent").grid(row=2, column=2, padx=5, sticky="w")

        # Mark Attendance Button
        ttk.Button(mark_frame, text="Mark My Attendance", command=self.mark_attendance_action_employee).grid(row=3, column=0, columnspan=3, pady=15, sticky="ew")

        # Instructions/Notes
        ttk.Label(mark_frame, text="Note: You can mark your attendance for today or a past date. Marking attendance for a date that already has a record will update it.",
                  font=FONT_SMALL, wraplength=450, foreground=COLOR_TEXT).grid(row=4, column=0, columnspan=3, pady=5, sticky="w")


    def mark_attendance_action_employee(self):
        print(f"DEBUG: mark_attendance_action_employee called. self.mark_status_var exists: {hasattr(self, 'mark_status_var')}")
        """Action specifically for employees to mark their own attendance."""
        emp_id = self.current_user # Directly use the logged-in employee's ID
        date = self.emp_self_mark_date_entry.get_date().strftime('%Y-%m-%d')
        status = self.mark_status_var.get() # Access the pre-initialized StringVar

        if not all([date, status]):
            messagebox.showerror("Input Error", "Please select a date and status.")
            return

        try:
            mark_attendance(emp_id, date, status)
            self.load_employee_attendance_history() # Refresh history in 'Your Attendance' tab
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while marking attendance: {e}")


    def setup_employee_password_tab(self, parent_frame):
        password_frame = ttk.LabelFrame(parent_frame, text="Change Your Password", padding="15", style='TFrame')
        password_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(password_frame, text="New Password:").grid(row=0, column=0, sticky="w", pady=5)
        self.new_password_entry = ttk.Entry(password_frame, show="*", width=30)
        self.new_password_entry.grid(row=0, column=1, pady=5)

        ttk.Label(password_frame, text="Confirm New Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.confirm_new_password_entry = ttk.Entry(password_frame, show="*", width=30)
        self.confirm_new_password_entry.grid(row=1, column=1, pady=5)

        ttk.Button(password_frame, text="Change Password", command=self.change_employee_password).grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

    def change_employee_password(self):
        new_pass = self.new_password_entry.get()
        confirm_pass = self.confirm_new_password_entry.get()

        if not new_pass or not confirm_pass:
            messagebox.showerror("Input Error", "Please fill in both password fields.")
            return

        if new_pass != confirm_pass:
            messagebox.showerror("Password Mismatch", "New password and confirmation do not match.")
            return

        if update_employee_password(self.current_user, new_pass):
            messagebox.showinfo("Success", "Your password has been changed successfully!")
            self.new_password_entry.delete(0, tk.END)
            self.confirm_new_password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Failed to change password. Please try again.")

    def load_employee_attendance_history(self):
        """Loads the current employee's attendance into the Treeview."""
        for i in self.employee_attendance_tree.get_children():
            self.employee_attendance_tree.delete(i)
        attendance_records = get_attendance_by_employee(self.current_user)
        for record in attendance_records:
            self.employee_attendance_tree.insert("", "end", values=record)

    def show_employee_monthly_summary(self):
        year_str = self.emp_summary_year_entry.get()
        month_str = self.emp_summary_month_entry.get()

        if not all([year_str, month_str]):
            self.emp_summary_label.config(text="Please enter year and month.")
            return

        try:
            year = int(year_str)
            month = int(month_str)
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12.")
        except ValueError as e:
            self.emp_summary_label.config(text=f"Invalid input: {e}", foreground=COLOR_ERROR)
            return

        percentage = get_monthly_attendance_percentage(self.current_user, year, month)
        salary = calculate_salary(self.current_user, year, month)

        summary_text = (f"Attendance for {month}/{year}:\n"
                        f"Percentage: {percentage:.2f}%\n"
                        f"Calculated Salary: {salary:,.2f}")
        self.emp_summary_label.config(text=summary_text, foreground=COLOR_TEXT)


# --- Main execution ---
if __name__ == "__main__":
    init_db() # Initialize database and preload data
    root = tk.Tk()
    app = EmployeeAttendanceApp(root)
    root.mainloop()