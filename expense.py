import streamlit as st
import pyodbc
import bcrypt
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import os

# Page config
st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰")

# Database connection
server_name = "XYZ-PC"
database_name = "ExpenseTracker"
conn = pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={database_name};Trusted_Connection=yes;")
cursor = conn.cursor()

# --- Functions ---

def create_users_table():
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
    CREATE TABLE Users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) UNIQUE NOT NULL,
        password VARBINARY(255) NOT NULL
    );
    """)
    conn.commit()

def create_expenses_table():
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Expenses' AND xtype='U')
    CREATE TABLE Expenses (
        id INT IDENTITY(1,1) PRIMARY KEY,
        date DATE NOT NULL,
        description NVARCHAR(255) NOT NULL,
        category NVARCHAR(50) NOT NULL,
        amount FLOAT NOT NULL,
        username NVARCHAR(50) NOT NULL
    );
    """)
    conn.commit()

def create_user_audit_table():
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='UserAudit' AND xtype='U')
    CREATE TABLE UserAudit (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) NOT NULL,
        deleted_at DATETIME NOT NULL
    );
    """)
    conn.commit()

def create_user_delete_trigger():
    cursor.execute("""
    IF OBJECT_ID('TR_DeleteUserAudit', 'TR') IS NULL
    EXEC('CREATE TRIGGER TR_DeleteUserAudit ON Users AFTER DELETE AS BEGIN SET NOCOUNT ON; END')
    """)

    cursor.execute("""
    ALTER TRIGGER TR_DeleteUserAudit
    ON Users
    AFTER DELETE
    AS
    BEGIN
        INSERT INTO UserAudit (username, deleted_at)
        SELECT username, GETDATE() FROM DELETED;

        DELETE FROM Expenses
        WHERE username IN (SELECT username FROM DELETED);
    END;
    """)
    conn.commit()

def register_user(username, password):
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except:
        return False

def authenticate_user(username, password):
    cursor.execute("SELECT password FROM Users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result:
        return bcrypt.checkpw(password.encode('utf-8'), result[0])
    return False

def add_expense(description, category, amount, username):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("EXEC AddExpense ?, ?, ?, ?, ?", (date, description, category, amount, username))
    conn.commit()

def fetch_expenses(username):
    if username == "admin":
        return pd.read_sql("EXEC GetAllExpenses", conn)
    return pd.read_sql("EXEC GetExpensesByUser ?", conn, params=[username])

def delete_user_and_expenses(username):
    cursor.execute("DELETE FROM Users WHERE username = ?", (username,))
    conn.commit()

# Dashboard summary for admin
def generate_dashboard_summary(df):
    return {
        "Total Expenses": df['amount'].sum(),
        "Total Users": df['username'].nunique(),
        "Top Spenders": df.groupby('username')['amount'].sum().sort_values(ascending=False).head(3),
        "Category Breakdown": df.groupby('category')['amount'].sum(),
        "Monthly Trend": df.groupby(pd.to_datetime(df['date']).dt.to_period("M"))['amount'].sum()
    }

# PDF Report Generator
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Expense Report', ln=True, align='C')
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 9)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def expense_table(self, df):
        self.set_font('Arial', 'B', 12)
        self.cell(30, 10, 'Date', 1)
        self.cell(50, 10, 'Description', 1)
        self.cell(40, 10, 'Category', 1)
        self.cell(30, 10, 'Amount', 1)
        self.ln()

        self.set_font('Arial', '', 11)
        for _, row in df.iterrows():
            y_before = self.get_y()
            self.multi_cell(50, 8, row['description'], 1)
            y_after = self.get_y()
            height = y_after - y_before

            self.set_y(y_before)
            self.cell(30, height, str(row['date'])[:10], 1)
            self.set_x(30 + 50)
            self.cell(40, height, row['category'], 1)
            self.cell(30, height, f"${row['amount']:.2f}", 1)
            self.ln(height)

def generate_pdf_report(df, username):
    user_df = df if username == 'admin' else df[df['username'] == username]
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"User: {username}", ln=True)
    pdf.cell(0, 10, f"Total Expenses: ${user_df['amount'].sum():.2f}", ln=True)
    pdf.ln(5)
    pdf.expense_table(user_df)
    filename = f"{username}_expense_report.pdf"
    pdf.output(filename)
    return filename

# Initialize tables and trigger
create_users_table()
create_expenses_table()
create_user_audit_table()
create_user_delete_trigger()

# --- UI ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("Expense Tracker Login")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        login_username = st.text_input("Username")
        login_password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(login_username, login_password):
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        reg_username = st.text_input("New Username")
        reg_password = st.text_input("New Password", type="password")
        if st.button("Register"):
            if register_user(reg_username, reg_password):
                st.success("Registration successful! Please log in.")
            else:
                st.error("Username already exists. Try another.")

else:
    st.title("Personal Expense Tracker")
    st.write(f"Welcome, {st.session_state.username}!")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Add Expense
    with st.form("add_expense_form", clear_on_submit=True):
        st.header("Add New Expense")
        description = st.text_input("Description")
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Other"])
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        submit = st.form_submit_button("Add Expense")
        if submit and description and amount > 0:
            add_expense(description, category, amount, st.session_state.username)
            st.success("Expense added successfully!")
            st.rerun()

    # View Expenses
    st.header("Your Expenses")
    expenses = fetch_expenses(st.session_state.username)
    st.dataframe(expenses)

    # Admin Dashboard
    if st.session_state.username == "admin":
        st.subheader("📊 Admin Dashboard Summary")
        summary = generate_dashboard_summary(expenses)
        st.metric("Total Expenses", f"${summary['Total Expenses']:.2f}")
        st.metric("Total Users", summary["Total Users"])
        st.subheader("🏆 Top Spenders")
        st.dataframe(summary["Top Spenders"])
        st.subheader("📂 Category Breakdown")
        st.bar_chart(summary["Category Breakdown"])
        st.subheader("📈 Monthly Trend")
        st.line_chart(summary["Monthly Trend"])

        # Admin user delete
        st.subheader("Delete User")
        all_users = pd.read_sql("SELECT username FROM Users WHERE username != 'admin'", conn)
        user_to_delete = st.selectbox("Select a user to delete", all_users['username'])

        with st.expander("⚠ Confirm Deletion"):
            confirm_delete = st.checkbox("Yes, I want to delete this user and their expenses.")
            if st.button("Delete Selected User"):
                if user_to_delete and confirm_delete:
                    delete_user_and_expenses(user_to_delete)
                    st.success(f"User '{user_to_delete}' and their expenses have been deleted.")
                    st.rerun()
                elif not confirm_delete:
                    st.warning("Please check the confirmation box to proceed.")

    # PDF Export
    st.subheader("📄 Generate PDF Report")
    if st.button("📂 Download PDF Report"):
        filename = generate_pdf_report(expenses, st.session_state.username)
        with open(filename, "rb") as f:
            st.download_button("Download Report", f, file_name=filename, mime="application/pdf")
        os.remove(filename)