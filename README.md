# Vibrant Personal Expense Tracker

A modern, stylish, and powerful desktop application for tracking your personal finances. Built with Python, CustomTkinter, and Matplotlib, this app provides a beautiful and intuitive interface to manage your income, expenses, and budgets, all while saving your data locally.

---

## 🚀 How to Run (Recommended Method)

No setup required! The easiest way to run this application is by using the pre-compiled executable:

1. Navigate to the `dist` folder in the project directory.  
2. Double-click the `gui_expense_tracker.exe` file.  
3. The application will start immediately.  

That's it! You do not need to install Python or any of the libraries listed below to run the `.exe` file.

---

## ✨ Features

This application is more than just a simple ledger. It's a full-featured financial dashboard.

### 1. Modern "Fintech" Dashboard
- **KPI Cards:** Instantly see your total Income, Expense, and Net Savings for the current month, with vibrant colors to guide you.
- **Vibrant Donut Chart:** A beautiful, auto-generating donut chart (via Matplotlib) visualizes your exact spending breakdown by category.
- **Budget Progress Bars:** The dashboard shows a real-time progress bar for every budget you've set, allowing you to see how much you've spent (e.g., Groceries: $350 / $500) at a glance.

### 2. Full Transaction Management
- **Add Transactions:** A clean form allows you to quickly add new Income or Expense entries using a stylish toggle.
- **View All Transactions:** A dedicated, scrollable page lists all your transactions in history, sorted by date. Expenses are highlighted in red and income in green.

### 3. Powerful Settings & Customization
- **Global Currency Selector:** Choose your preferred currency from a dropdown (USD, EUR, GBP, INR, JPY). The currency symbol instantly updates across the entire application.
- **Category Management:** Add, view, and manage your own custom categories for both income and expenses.
- **Budget Management:** Set monthly spending limits for any of your expense categories. These budgets automatically link to the progress bars on the dashboard.

### 4. Persistent Local Storage
- **Automatic Saving:** All your data—transactions, custom categories, budgets, and currency preference—is automatically saved to an `expense_data.json` file in the same directory. Your data is always persistent every time you open the app.

---

## 🧑‍💻 How to Run (Developer Mode)

If you want to run the application from the source code or make your own modifications, follow these steps:

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### 1. Clone or Download the Repository
```bash
git clone https://your-repo-url/expense-tracker.git
cd expense-tracker
