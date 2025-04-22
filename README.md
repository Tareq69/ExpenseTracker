# Personal Expense Tracker with SQL Integration

This is a Personal Expense Tracker app built with Streamlit and MS SQL Server integration. It helps you easily track your daily expenses, edit them, and view your spending habits. The app connects to an MS SQL Server database for storing and managing your expenses, offering a professional, user-friendly interface to maintain your finances.

# Features

<li><b>Add Expenses:</b> Record your expenses with description, category, and amount.</li>
<li><b>Edit Expenses:</b> Modify any expense detail when necessary.</li>
<li><b>Delete Expenses:</b> Remove any unwanted or incorrect expenses.</li>
<li><b>Auto Date Tracking:</b> Automatically adds the current date to each expense.</li>
<li><b>Expense Grouping by Date:</b> Displays expenses grouped by the date they were added.</li>
<li><b>Download Data:</b> Export your expense data as a CSV file for backup or analysis.</li>

# Technology Stack Used

<li><b>Streamlit:</b> For building the user interface.</li>
<li><b>MS SQL Server:</b> To store and manage your expense data securely.</li>
<li><b>PyODBC:</b> Used for connecting to the MS SQL Server database via Python.</li>

# How to Use

<li><b>Run the App:</b> Execute the expense.py file using Python.</li>
<li><b>Add an Expense:</b> Click the "Add Expense" button, enter your details, and submit.</li>
<li><b>Edit an Expense:</b> Click on the edit button next to an expense to make changes.</li>
<li><b>Delete an Expense:</b> Click the delete button to remove any expense.</li>
<li><b>Download Your Data:</b> Click the "Download CSV" button to export your data.</li>

# Setup Instructions

## Install the required Python packages:
```bash
pip install streamlit pyodbc
```
Ensure your MS SQL Server is set up and running.
Update the expense.py file with your server name and database name in the connection string.

## Run the app using:
```bash
streamlit run expense.py
```
# License
This project is licensed under the MIT License. See the <a href="LICENSE" target="_blank">LICENSE</a> file for more details.
