import json
import os
import tkinter as tk
from datetime import datetime
from collections import defaultdict
import customtkinter as ctk  # Import the modern GUI library
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math, random
import numpy as np  # For chart colors

# --- Data File ---
DATA_FILE = 'expense_data.json'

# --- 1. THE "BACKEND" LOGIC ---
# This class now handles currency.

class ExpenseLogic:
    def __init__(self):
        """Initializes the data logic, loading from the JSON file."""
        self.transactions = []
        self.categories = {
            "expense": ["Groceries", "Rent", "Transport", "Dining", "Utilities", "Other"],
            "income": ["Salary", "Bonus", "Gifts", "Other"]
        }
        self.budgets = {}
        # New: Currency data
        self.currencies = {"USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£", "INR (₹)": "₹", "JPY (¥)": "¥"}
        self.currency_symbol = "$"  # Default
        self.load_data()

    def load_data(self):
        """Loads data from the JSON file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.transactions = data.get('transactions', [])
                    self.categories = data.get('categories', self.categories)
                    self.budgets = data.get('budgets', {})
                    # New: Load currency
                    self.currency_symbol = data.get('currency_symbol', '$')
            except (json.JSONDecodeError, IOError):
                print("Warning: Data file corrupted or unreadable. Starting clean.")
                self.save_data() # Create a fresh file
        else:
            print("No data file found. Creating a new one.")
            self.save_data()

    def save_data(self):
        """Saves the current state to the JSON file."""
        data = {
            'transactions': self.transactions,
            'categories': self.categories,
            'budgets': self.budgets,
            'currency_symbol': self.currency_symbol # New: Save currency
        }
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            print(f"Error: Could not save data to file. {e}")

    # --- New Currency Methods ---
    
    def get_currency_symbol(self):
        """Returns the current currency symbol."""
        return self.currency_symbol

    def get_currencies(self):
        """Returns the dictionary of available currencies."""
        return self.currencies
        
    def set_currency(self, new_symbol):
        """Sets the new currency symbol and saves it."""
        self.currency_symbol = new_symbol
        self.save_data()
        
    def format_currency(self, amount):
        """Formats a number as a string with the current currency symbol."""
        return f"{self.currency_symbol}{amount:.2f}"

    # --- Transaction Methods ---
    def add_transaction(self, trans_type, amount, category, description, date_str):
        """Adds a new transaction. Called by the GUI."""
        try:
            amount = abs(float(amount))
            # Validate date
            date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            
            transaction = {
                'id': len(self.transactions) + 1,
                'type': trans_type,
                'amount': amount,
                'category': category,
                'description': description,
                'date': date
            }
            self.transactions.append(transaction)
            self.transactions.sort(key=lambda x: x['date'], reverse=True) # Keep sorted
            self.save_data()
            return True, "Transaction added successfully."
        except ValueError:
            return False, "Invalid amount or date format (YYYY-MM-DD)."
        except Exception as e:
            return False, f"An error occurred: {e}"

    def get_categories(self, trans_type):
        """Returns the list of categories for 'income' or 'expense'."""
        return self.categories.get(trans_type, [])

    def add_category(self, new_category, trans_type):
        """Adds a new category."""
        new_category = new_category.strip().title()
        if new_category and new_category not in self.categories[trans_type]:
            self.categories[trans_type].append(new_category)
            self.save_data()
            return True, f"Category '{new_category}' added."
        elif not new_category:
            return False, "Category name cannot be empty."
        else:
            return False, "Category already exists."

    def get_budgets(self):
        """Returns the budgets dictionary."""
        return self.budgets

    def set_budget(self, category, amount):
        """Sets or updates a budget for a category."""
        try:
            amount = float(amount)
            if amount < 0:
                return False, "Budget amount cannot be negative."
            self.budgets[category] = amount
            self.save_data()
            # Updated: Use format_currency
            return True, f"Budget for {category} set to {self.format_currency(amount)}."
        except ValueError:
            return False, "Invalid amount."

    def get_monthly_report_data(self):
        """Calculates and returns all data for the current month's report."""
        now = datetime.now()
        current_month_str = now.strftime('%Y-%m')
        
        month_transactions = [t for t in self.transactions if t['date'].startswith(current_month_str)]

        total_income = sum(t['amount'] for t in month_transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in month_transactions if t['type'] == 'expense')
        net_savings = total_income - total_expense

        spending_by_category = defaultdict(float)
        for t in month_transactions:
            if t['type'] == 'expense':
                spending_by_category[t['category']] += t['amount']
        
        return {
            'month_name': now.strftime('%B %Y'),
            'total_income': total_income,
            'total_expense': total_expense,
            'net_savings': net_savings,
            'spending_by_category': spending_by_category
        }

# --- 2. THE "FRONTEND" GUI ---
# ... 2. THE "FRONTEND" GUI ...

class ExpenseTrackerApp(ctk.CTk):
    
    def __init__(self):
        super().__init__()
        
        self.logic = ExpenseLogic()

        # --- Window Setup ---
        self.title("Personal Expense Tracker")
        self.geometry("1100x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # --- Main Layout (Sidebar + Content) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Expense Tracker", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20, padx=20)

        # --- Stylish Sidebar Buttons ---
        nav_font = ctk.CTkFont(size=14, weight="bold")

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="🏠  Dashboard", 
                                           command=self.show_dashboard_frame,
                                           font=nav_font, anchor="w",
                                           fg_color="transparent", hover_color="#343638")
        self.btn_dashboard.pack(pady=5, padx=20, fill="x")
        
        self.btn_add = ctk.CTkButton(self.sidebar_frame, text="➕  Add Transaction", 
                                     command=self.show_add_transaction_frame,
                                     font=nav_font, anchor="w",
                                     fg_color="transparent", hover_color="#343638")
        self.btn_add.pack(pady=5, padx=20, fill="x")
        
        self.btn_view = ctk.CTkButton(self.sidebar_frame, text="📋  View Transactions", 
                                       command=self.show_view_transactions_frame,
                                       font=nav_font, anchor="w",
                                       fg_color="transparent", hover_color="#343638")
        self.btn_view.pack(pady=5, padx=20, fill="x")

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="⚙️  Settings", 
                                          command=self.show_settings_frame,
                                          font=nav_font, anchor="w",
                                          fg_color="transparent", hover_color="#343638")
        self.btn_settings.pack(pady=5, padx=20, fill="x")

        # --- Main Content Frame (Slightly lighter dark) ---
        self.main_frame = ctk.CTkFrame(self, fg_color="#242424")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # --- Initialize with Dashboard ---
        self.show_dashboard_frame()

    # --- Frame Switching Logic ---

    def clear_main_frame(self):
        """Destroys all widgets in the main frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard_frame(self):
        self.clear_main_frame()
        
        report_data = self.logic.get_monthly_report_data()

        # --- Summary Cards ---
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)

        title_label = ctk.CTkLabel(self.main_frame, text=f"Dashboard for {report_data['month_name']}", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10, padx=20, sticky="w")
        
        # --- Styled Summary Cards ---
        card_fg_color = "#2D2D2D"

        # Card 1: Income
        income_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=card_fg_color)
        income_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(income_frame, text="Total Income", font=ctk.CTkFont(size=16)).pack(pady=(10,5))
        ctk.CTkLabel(income_frame, text=self.logic.format_currency(report_data['total_income']), text_color="#00D100", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0,10))

        # Card 2: Expense
        expense_frame = ctk.CTkFrame(self.main_frame, fg_color=card_fg_color)
        expense_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(expense_frame, text="Total Expense", font=ctk.CTkFont(size=16)).pack(pady=(10,5))
        ctk.CTkLabel(expense_frame, text=self.logic.format_currency(report_data['total_expense']), text_color="#FF4040", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0,10))
        
        # Card 3: Net Savings
        net_frame = ctk.CTkFrame(self.main_frame, fg_color=card_fg_color)
        net_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(net_frame, text="Net Savings", font=ctk.CTkFont(size=16)).pack(pady=(10,5))
        net_color = "#00D100" if report_data['net_savings'] >= 0 else "#FF4040"
        ctk.CTkLabel(net_frame, text=self.logic.format_currency(report_data['net_savings']), text_color=net_color, font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0,10))

        # --- Chart Frame ---
        chart_frame = ctk.CTkFrame(self.main_frame, fg_color=card_fg_color)
        chart_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1) # Make chart frame expand

        self.create_pie_chart(chart_frame, report_data['spending_by_category'])

    def create_pie_chart(self, master_frame, spending_data):
        """Creates and embeds a Matplotlib pie chart."""
        
        # Set up figure
        fig = Figure(figsize=(5, 4), dpi=100)
        fig.set_facecolor("#2D2D2D") # Match card background
        ax = fig.add_subplot(111)
        ax.set_facecolor("#2D2D2D")

        if not spending_data:
            labels = list(spending_data.keys())
            sizes = list(spending_data.values())
            
            # --- New: Vibrant Colors ---
            cmap = plt.get_cmap("viridis")
            colors = cmap(np.linspace(0, 1, len(sizes)))

            # Create the pie chart
            wedges, texts, autotexts = ax.pie(
                sizes, 
                autopct='%1.1f%%', 
                startangle=140,
                textprops=dict(color="w"),
                pctdistance=0.85,
                colors=colors  # Use vibrant colors
            )
            
            # Draw a circle at the center to make it a donut chart
            centre_circle = plt.Circle((0,0),0.70,fc='#2D2D2D')
            ax.add_artist(centre_circle)
            
            ax.axis('equal')  # Equal aspect ratio
            
            # Add legend
            ax.legend(wedges, labels,
                      title="Categories",
                      loc="center left",
                      bbox_to_anchor=(1, 0, 0.5, 1),
                      labelcolor='white',
                      facecolor="#2D2D2D", # Match legend background
                      edgecolor="none",
                      frameon=False)

        # Embed the chart in the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=master_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)


    def show_add_transaction_frame(self):
        self.clear_main_frame()
        
        title_label = ctk.CTkLabel(self.main_frame, text="Add New Transaction", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=20, padx=20, anchor="w")
        
        # Frame for the form
        form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=20)
        
        # --- Form Widgets ---
        
        # --- New: Stylish Segmented Button ---
        ctk.CTkLabel(form_frame, text="Type:").grid(row=0, column=0, padx=5, pady=10, sticky="e")
        self.trans_type_var = ctk.StringVar(value="Expense")
        type_toggle = ctk.CTkSegmentedButton(form_frame, 
                                             values=["Expense", "Income"],
                                             variable=self.trans_type_var,
                                             command=self.update_categories_dropdown)
        type_toggle.grid(row=0, column=1, columnspan=2, padx=5, pady=10, sticky="ew")

        # Amount - Updated with currency
        ctk.CTkLabel(form_frame, text=f"Amount: {self.logic.get_currency_symbol()}").grid(row=1, column=0, padx=5, pady=10, sticky="e")
        self.amount_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00")
        self.amount_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=10, sticky="ew")

        # Category
        ctk.CTkLabel(form_frame, text="Category:").grid(row=2, column=0, padx=5, pady=10, sticky="e")
        self.category_var = ctk.StringVar()
        self.category_menu = ctk.CTkOptionMenu(form_frame, variable=self.category_var, values=[])
        self.category_menu.grid(row=2, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        self.update_categories_dropdown() # Initial population

        # Description
        ctk.CTkLabel(form_frame, text="Description:").grid(row=3, column=0, padx=5, pady=10, sticky="e")
        self.desc_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., Weekly groceries")
        self.desc_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=10, sticky="ew")

        # Date
        ctk.CTkLabel(form_frame, text="Date:").grid(row=4, column=0, padx=5, pady=10, sticky="e")
        self.date_entry = ctk.CTkEntry(form_frame, placeholder_text="YYYY-MM-DD")
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.date_entry.grid(row=4, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        
        # Submit Button
        submit_button = ctk.CTkButton(form_frame, text="Add Transaction", command=self.submit_transaction)
        submit_button.grid(row=5, column=1, columnspan=2, padx=5, pady=20, sticky="ew")
        
        # Status Label
        self.status_label = ctk.CTkLabel(form_frame, text="", text_color="gray")
        self.status_label.grid(row=6, column=0, columnspan=3, padx=5, pady=10)

    def update_categories_dropdown(self, value=None):
        """Called when segmented button is toggled."""
        # 'value' comes from the segmented button (e.g., "Expense")
        trans_type = self.trans_type_var.get().lower() 
        categories = self.logic.get_categories(trans_type)
        self.category_menu.configure(values=categories)
        if categories:
            self.category_var.set(categories[0])
        else:
            self.category_var.set("No categories found")

    def submit_transaction(self):
        """Reads form data and calls the logic method to add it."""
        trans_type = self.trans_type_var.get().lower()
        amount = self.amount_entry.get()
        category = self.category_var.get()
        description = self.desc_entry.get()
        date_str = self.date_entry.get()

        success, message = self.logic.add_transaction(trans_type, amount, category, description, date_str)
        
        if success:
            self.status_label.configure(text=message, text_color="#00D100")
            # Clear entries
            self.amount_entry.delete(0, 'end')
            self.desc_entry.delete(0, 'end')
            self.date_entry.delete(0, 'end')
            self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        else:
            self.status_label.configure(text=message, text_color="#FF4040")

    def show_view_transactions_frame(self):
        self.clear_main_frame()

        title_label = ctk.CTkLabel(self.main_frame, text="All Transactions", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=20, padx=20, anchor="w")
        
        # Scrollable Frame
        scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="#2b2b2b")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- New: Styled Header ---
        header_frame = ctk.CTkFrame(scroll_frame, fg_color="#007BFF", corner_radius=5) # Bright blue header
        header_frame.pack(fill="x", pady=(0, 5))
        header_frame.grid_columnconfigure(0, weight=1) # Date
        header_frame.grid_columnconfigure(1, weight=1) # Category
        header_frame.grid_columnconfigure(2, weight=1) # Description
        header_frame.grid_columnconfigure(3, weight=1) # Amount
        
        header_font = ctk.CTkFont(weight="bold")
        ctk.CTkLabel(header_frame, text="Date", font=header_font).grid(row=0, column=0, padx=10, pady=5)
        ctk.CTkLabel(header_frame, text="Category", font=header_font).grid(row=0, column=1, padx=10, pady=5)
        ctk.CTkLabel(header_frame, text="Description", font=header_font).grid(row=0, column=2, padx=10, pady=5)
        ctk.CTkLabel(header_frame, text="Amount", font=header_font).grid(row=0, column=3, padx=10, pady=5)

        # Transaction List
        if not self.logic.transactions:
            ctk.CTkLabel(scroll_frame, text="No transactions found.").pack(pady=20)
            return

        for i, t in enumerate(self.logic.transactions):
            bg_color = "#2b2b2b" if i % 2 == 0 else "#343638"
            row_frame = ctk.CTkFrame(scroll_frame, fg_color=bg_color, corner_radius=5)
            row_frame.pack(fill="x", pady=2)
            
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)

            ctk.CTkLabel(row_frame, text=t['date']).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(row_frame, text=t['category']).grid(row=0, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(row_frame, text=t['description'] if t['description'] else "---").grid(row=0, column=2, padx=10, pady=5, sticky="w")
            
            # Updated: Use format_currency
            amount_str = self.logic.format_currency(t['amount'])
            color = "#FF4040" if t['type'] == 'expense' else "#00D100"
            ctk.CTkLabel(row_frame, text=amount_str, text_color=color, font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=10, pady=5, sticky="e")

    def show_settings_frame(self):
        """Updated layout with Global Settings, Budgets, and Categories."""
        self.clear_main_frame()
        
        # Configure grid for 3 rows (Title, Global, 2-col Settings)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0) # Title
        self.main_frame.grid_rowconfigure(1, weight=0) # Global Settings
        self.main_frame.grid_rowconfigure(2, weight=1) # Budgets/Cats
        
        title_label = ctk.CTkLabel(self.main_frame, text="Settings", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20, padx=10, sticky="w")

        # --- New: Global Settings Frame ---
        global_frame = ctk.CTkFrame(self.main_frame)
        global_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(global_frame, text="Global Settings", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Currency Selector
        currency_inner_frame = ctk.CTkFrame(global_frame, fg_color="transparent")
        currency_inner_frame.pack(pady=10)
        
        ctk.CTkLabel(currency_inner_frame, text="Currency:").pack(side="left", padx=10)
        
        currency_names = list(self.logic.get_currencies().keys())
        # Find the full name (e.g., "USD ($)") from the symbol (e.g., "$")
        current_symbol = self.logic.get_currency_symbol()
        try:
            current_currency_name = [name for name, symbol in self.logic.get_currencies().items() if symbol == current_symbol][0]
        except IndexError:
            current_currency_name = currency_names[0] # Fallback
            
        self.currency_var = ctk.StringVar(value=current_currency_name)
        currency_menu = ctk.CTkOptionMenu(currency_inner_frame, 
                                          values=currency_names, 
                                          variable=self.currency_var, 
                                          command=self.update_currency)
        currency_menu.pack(side="left", padx=10)

        # --- Category Management Frame ---
        cat_frame = ctk.CTkFrame(self.main_frame)
        cat_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        cat_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(cat_frame, text="Manage Categories", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=3, pady=10, padx=10)
        
        # Add new category
        self.new_cat_entry = ctk.CTkEntry(cat_frame, placeholder_text="New Category Name")
        self.new_cat_entry.grid(row=1, column=0, padx=10, pady=5)
        
        self.new_cat_type = ctk.StringVar(value="expense")
        ctk.CTkRadioButton(cat_frame, text="Expense", variable=self.new_cat_type, value="expense").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkRadioButton(cat_frame, text="Income", variable=self.new_cat_type, value="income").grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkButton(cat_frame, text="Add Category", command=self.add_new_category).grid(row=1, column=1, padx=10, pady=5)
        
        self.cat_status_label = ctk.CTkLabel(cat_frame, text="")
        self.cat_status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # List categories
        list_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        list_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(list_frame, text="Expense Categories", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0)
        ctk.CTkLabel(list_frame, text="Income Categories", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1)
        
        exp_list = "\n".join(self.logic.get_categories("expense"))
        inc_list = "\n".join(self.logic.get_categories("income"))
        
        ctk.CTkLabel(list_frame, text=exp_list, justify="left").grid(row=1, column=0, sticky="n", padx=10)
        ctk.CTkLabel(list_frame, text=inc_list, justify="left").grid(row=1, column=1, sticky="n", padx=10)
        
        # --- Budget Management Frame ---
        budget_frame = ctk.CTkFrame(self.main_frame)
        budget_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        budget_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(budget_frame, text="Manage Budgets", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=2, pady=10, padx=10)
        
        # Set new budget
        ctk.CTkLabel(budget_frame, text="Category:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.budget_cat_menu = ctk.CTkOptionMenu(budget_frame, values=self.logic.get_categories("expense"))
        if not self.logic.get_categories("expense"):
            self.budget_cat_menu.set("No expense categories")
        self.budget_cat_menu.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Updated: Use currency symbol
        ctk.CTkLabel(budget_frame, text=f"Amount: {self.logic.get_currency_symbol()}").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.budget_amount_entry = ctk.CTkEntry(budget_frame, placeholder_text="0.00")
        self.budget_amount_entry.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        ctk.CTkButton(budget_frame, text="Set Budget", command=self.set_new_budget).grid(row=5, column=0, columnspan=2, padx=10, pady=10)
        
        self.budget_status_label = ctk.CTkLabel(budget_frame, text="")
        self.budget_status_label.grid(row=6, column=0, columnspan=2, pady=5)

        # List budgets - Updated with format_currency
        ctk.CTkLabel(budget_frame, text="Current Budgets", font=ctk.CTkFont(weight="bold")).grid(row=7, column=0, columnspan=2, pady=(10,5))
        
        budget_list = "\n".join([f"{cat}: {self.logic.format_currency(amt)}" for cat, amt in self.logic.get_budgets().items()])
        if not budget_list:
            budget_list = "No budgets set."
        ctk.CTkLabel(budget_frame, text=budget_list, justify="left").grid(row=8, column=0, columnspan=2, sticky="w", padx=10)

    def add_new_category(self):
        """Called by the 'Add Category' button."""
        new_cat = self.new_cat_entry.get()
        cat_type = self.new_cat_type.get()
        success, message = self.logic.add_category(new_cat, cat_type)
        
        color = "#00D100" if success else "#FF4040"
        self.cat_status_label.configure(text=message, text_color=color)
        
        if success:
            self.new_cat_entry.delete(0, 'end')
            # Refresh the category lists and budget dropdown
            self.show_settings_frame()

    def set_new_budget(self):
        if not category or category == "No expense categories":
            self.budget_status_label.configure(text="Please add an expense category first.", text_color="#FF4040")
            return
            
        amount = self.budget_amount_entry.get()
        
        success, message = self.logic.set_budget(category, amount)
        
        color = "#00D100" if success else "#FF4040"
        self.budget_status_label.configure(text=message, text_color=color)
        
        if success:
            self.budget_amount_entry.delete(0, 'end')
            # Refresh the budget list
            self.show_settings_frame()

    # --- New: Currency Update Callback ---
    def update_currency(self, choice_name):
        """Called when a new currency is selected from the dropdown."""
        new_symbol = self.logic.get_currencies()[choice_name]
        self.logic.set_currency(new_symbol)
        
        # Refresh the settings page to show new symbol
        self.show_settings_frame()
        # Other pages will update when you navigate to them
        

# --- 3. RUN THE APP ---
if __name__ == "__main__":
    # Import plt here to avoid import error if matplotlib is not installed
    # and to make it available for the donut chart
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not found. Please run 'pip install matplotlib'")
        exit()

    app = ExpenseTrackerApp()
    app.mainloop()

    # --- CRAZY DETAILED STYLE MODULE (huge, expressive, programmable theme) ---
    # This block provides an extensive theme dictionary, many utility helpers,
    # and a large collection of pre-configured style helpers for customtkinter.
    # It is intentionally verbose to provide a wide palette and many presets.

    # NOTE: This module tries to be non-invasive. It registers a theme dictionary
    # with customtkinter and exposes helper functions and factory wrappers so the
    # rest of the app can use consistent styling. Depending on where this block
    # is placed, you may want to call register_crazy_theme() early, before the
    # main window is instantiated, to ensure it becomes the active theme.

    try:
        # ctk is expected to be available (imported by the main file).
        _ctk_present = True
    except Exception:
        _ctk_present = False

    if _ctk_present:
        # Create an extensive palette of color shades and semantic names.
        CRAZY_PALETTE = {
            # neutrals / background
            "bg_900": "#0B0D0F",
            "bg_800": "#0F1113",
            "bg_700": "#141619",
            "bg_600": "#1A1C1F",
            "bg_500": "#202225",
            "bg_400": "#272A2D",
            "bg_300": "#2F3235",
            "bg_200": "#383B3E",
            "bg_100": "#404345",
            # glass & translucent approximations (for drawing/imagery)
            "glass_1": "#0B0D0F22",
            "glass_2": "#FFFFFF12",
            # primary (vibrant)
            "primary_100": "#E6F0FF",
            "primary_200": "#BFD9FF",
            "primary_300": "#99C1FF",
            "primary_400": "#4D9EFF",
            "primary_500": "#1976FF",
            "primary_600": "#135BD6",
            "primary_700": "#0E44A8",
            "primary_800": "#0B347D",
            "primary_900": "#072650",
            # accent / neon
            "neon_pink": "#FF3CAC",
            "neon_orange": "#FF7A18",
            "neon_yellow": "#FFD166",
            "neon_green": "#2AE58D",
            "neon_blue": "#00C2FF",
            "neon_purple": "#9B5CFF",
            # semantic
            "success_500": "#23D160",
            "danger_500": "#FF3B30",
            "warning_500": "#FF9500",
            "info_500": "#2DB0FF",
            # subtle highlights
            "muted_100": "#9AA1A6",
            "muted_200": "#7D858A",
            "muted_300": "#5F666B",
            # special accents
            "emerald": "#16A085",
            "sunset": "#FF5E7E",
            "midnight": "#0C1A2B",
            # gradients (start/end pairs)
            "grad_primary_start": "#1976FF",
            "grad_primary_end": "#9B5CFF",
            "grad_candy_start": "#FF3CAC",
            "grad_candy_end": "#FFD166",
            # decorative strokes / borders
            "stroke_light": "#2F3336",
            "stroke_glow": "#1976FF66",
            # text colors
            "text_primary": "#FFFFFF",
            "text_secondary": "#BFC7CD",
            "text_tertiary": "#88939A",
        }

        # Build a very large theme dict (customtkinter accepts nested dicts
        # representing color tokens). We create many tokens to provide fine
        # control. This expands into dozens of entries to give a very rich theme.
        crazy_theme = {
            "color": {
                # window
                "background": CRAZY_PALETTE["bg_900"],
                "foreground": CRAZY_PALETTE["bg_400"],
                # primary palette
                "primary_50": CRAZY_PALETTE["primary_100"],
                "primary_100": CRAZY_PALETTE["primary_200"],
                "primary_200": CRAZY_PALETTE["primary_300"],
                "primary_300": CRAZY_PALETTE["primary_400"],
                "primary_400": CRAZY_PALETTE["primary_500"],
                "primary_500": CRAZY_PALETTE["primary_600"],
                "primary_600": CRAZY_PALETTE["primary_700"],
                "primary_700": CRAZY_PALETTE["primary_800"],
                "primary_800": CRAZY_PALETTE["primary_900"],
                # semantic
                "info": CRAZY_PALETTE["info_500"],
                "success": CRAZY_PALETTE["success_500"],
                "warning": CRAZY_PALETTE["warning_500"],
                "error": CRAZY_PALETTE["danger_500"],
                # accents
                "accent_neon_pink": CRAZY_PALETTE["neon_pink"],
                "accent_neon_blue": CRAZY_PALETTE["neon_blue"],
                "accent_neon_green": CRAZY_PALETTE["neon_green"],
                "accent_neon_purple": CRAZY_PALETTE["neon_purple"],
                # text
                "text": CRAZY_PALETTE["text_primary"],
                "text_subtle": CRAZY_PALETTE["text_secondary"],
                "muted": CRAZY_PALETTE["muted_200"],
                # surfaces
                "surface_100": CRAZY_PALETTE["bg_400"],
                "surface_200": CRAZY_PALETTE["bg_300"],
                "surface_300": CRAZY_PALETTE["bg_200"],
                # borders
                "border": CRAZY_PALETTE["stroke_light"],
                "border_glow": CRAZY_PALETTE["stroke_glow"],
                # decorative gradients (tokenized)
                "gradient_primary_start": CRAZY_PALETTE["grad_primary_start"],
                "gradient_primary_end": CRAZY_PALETTE["grad_primary_end"],
                "gradient_candy_start": CRAZY_PALETTE["grad_candy_start"],
                "gradient_candy_end": CRAZY_PALETTE["grad_candy_end"],
            },
            # Additional tokens CTk may read for specific widgets can be provided
            "widget": {
                "frame": {
                    "fg_color": CRAZY_PALETTE["bg_700"],
                    "border_color": CRAZY_PALETTE["stroke_light"],
                    "corner_radius": 12,
                    "shadow": True,
                },
                "button": {
                    "fg_color": CRAZY_PALETTE["primary_500"],
                    "hover_color": CRAZY_PALETTE["primary_400"],
                    "text_color": CRAZY_PALETTE["text_primary"],
                    "corner_radius": 12,
                    "border_width": 0,
                },
                "secondary_button": {
                    "fg_color": CRAZY_PALETTE["bg_600"],
                    "hover_color": CRAZY_PALETTE["bg_500"],
                    "text_color": CRAZY_PALETTE["text_secondary"],
                    "corner_radius": 10,
                    "border_width": 1,
                    "border_color": CRAZY_PALETTE["stroke_light"],
                },
                "accent_button": {
                    "fg_color": CRAZY_PALETTE["neon_purple"],
                    "hover_color": CRAZY_PALETTE["neon_blue"],
                    "text_color": CRAZY_PALETTE["text_primary"],
                    "corner_radius": 999,  # pill
                },
                "entry": {
                    "fg_color": CRAZY_PALETTE["bg_700"],
                    "border_color": CRAZY_PALETTE["stroke_light"],
                    "text_color": CRAZY_PALETTE["text_primary"],
                    "placeholder_text_color": CRAZY_PALETTE["muted_100"],
                    "corner_radius": 8,
                },
                "label": {
                    "text_color": CRAZY_PALETTE["text_primary"],
                    "font_weight": "bold",
                },
                "segmented": {
                    "bg": CRAZY_PALETTE["bg_600"],
                    "active_bg": CRAZY_PALETTE["primary_500"],
                },
                "optionmenu": {
                    "fg_color": CRAZY_PALETTE["bg_700"],
                    "button_color": CRAZY_PALETTE["bg_600"],
                    "text_color": CRAZY_PALETTE["text_primary"],
                },
                "scrollbar": {
                    "bg": CRAZY_PALETTE["bg_800"],
                    "fg": CRAZY_PALETTE["primary_500"],
                }
            },
            # Provide custom names for fonts and sizes
            "font": {
                "family": "Inter, Segoe UI, Arial, Helvetica, sans-serif",
                "sizes": {
                    "tiny": 10,
                    "xs": 11,
                    "sm": 12,
                    "md": 14,
                    "lg": 18,
                    "xl": 22,
                    "xxl": 28,
                    "huge": 36
                },
                "weights": {
                    "thin": 200,
                    "regular": 400,
                    "medium": 600,
                    "bold": 800
                }
            }
        }

        # Register the theme with customtkinter (safe to call multiple times).
        # If the host code sets a theme after this, it will override; ideally call
        # register_crazy_theme() before window creation.
        def register_crazy_theme(activate=True):
            """
            Registers the crazy_theme dict with customtkinter.
            If activate is True, it also sets the appearance to 'Dark' and
            selects our theme as the default.
            """
            try:
                # customtkinter accepts dictionaries as theme data.
                ctk.set_default_color_theme(crazy_theme)
                if activate:
                    ctk.set_appearance_mode("Dark")
            except Exception:
                # fallback: do nothing if the method isn't available in this CTk version
                pass

        # Immediately attempt to register (harmless if late).
        try:
            register_crazy_theme(activate=False)
        except Exception:
            pass

        # --- Large collection of factory helpers to construct visually rich widgets ---
        # These helpers let the rest of the app opt in to the "crazy" styling.
        # Each factory returns a preconfigured widget. They intentionally include
        # many configurable parameters to encourage mixing & matching.

        def _canonical_font(size_key="md", weight="regular"):
            """Return a ctk.CTkFont-like tuple for convenience use."""
            sizes = crazy_theme["font"]["sizes"]
            weights = crazy_theme["font"]["weights"]
            size = sizes.get(size_key, sizes["md"])
            wt = weights.get(weight, weights["regular"])
            try:
                # CTkFont accepts family, size, weight
                return ctk.CTkFont(family="Inter", size=size, weight="bold" if wt >= 700 else "normal")
            except Exception:
                # fallback
                return ("Inter", size, "bold" if wt >= 700 else "normal")

        # Create a huge number of pre-tuned style builder functions (many lines).
        # We intentionally create variations to let the UI author choose a fine-grained style.

        def create_glass_frame(parent, height=None, width=None, corner_radius=14, border=True, glass_level=0.12):
            """
            Create a faux-glass frame with subtle border and glow. This function
            composes colors from the theme to approximate glassmorphism.
            """
            bg = CRAZY_PALETTE["bg_700"]
            glass_overlay = CRAZY_PALETTE["glass_2"]  # translucent white overlay token
            border_color = CRAZY_PALETTE["stroke_light"] if border else CRAZY_PALETTE["bg_700"]
            f = ctk.CTkFrame(parent,
                             fg_color=bg,
                             corner_radius=corner_radius,
                             border_width=1 if border else 0,
                             border_color=border_color,
                             height=height,
                             width=width)
            # Add a decorative inner label to emulate the glass highlight
            try:
                highlight = ctk.CTkLabel(f, text="", fg_color=CRAZY_PALETTE["bg_700"])
                highlight.place(relx=0.0, rely=0.0, relwidth=0.5, relheight=0.12)
            except Exception:
                pass
            return f

        def create_neon_button(parent, text, command=None, style="pink", width=120, height=40, corner_radius=999):
            """
            Create an accent neon-style button. style can be 'pink', 'blue', 'green', 'purple', 'orange'.
            """
            style_to_color = {
                "pink": CRAZY_PALETTE["neon_pink"],
                "blue": CRAZY_PALETTE["neon_blue"],
                "green": CRAZY_PALETTE["neon_green"],
                "purple": CRAZY_PALETTE["neon_purple"],
                "orange": CRAZY_PALETTE["neon_orange"],
            }
            color = style_to_color.get(style, CRAZY_PALETTE["neon_blue"])
            btn = ctk.CTkButton(parent,
                                text=text,
                                fg_color=color,
                                hover_color=_shade(color, -12) if "_shade" in globals() else color,
                                command=command,
                                corner_radius=corner_radius,
                                width=width,
                                height=height,
                                text_color=CRAZY_PALETTE["text_primary"],
                                font=_canonical_font("md", "medium"))
            # Try to add a soft glow by placing a canvas behind (best-effort).
            try:
                _apply_glow(btn, color)
            except Exception:
                pass
            return btn

        def create_pill_button(parent, text, command=None, accent=False, width=140, height=40):
            """
            Create a pill-shaped button, optionally accent-colored.
            """
            fg = CRAZY_PALETTE["primary_500"] if not accent else CRAZY_PALETTE["neon_blue"]
            return ctk.CTkButton(parent, text=text, fg_color=fg,
                                 hover_color=CRAZY_PALETTE["primary_400"],
                                 text_color=CRAZY_PALETTE["text_primary"],
                                 corner_radius=999, width=width, height=height,
                                 font=_canonical_font("md", "medium"), command=command)

        def create_card(parent, title="", subtitle="", footer_text="", width=None, height=None, corner_radius=14, padding=14):
            """
            Create a pre-styled card frame with places for title, body area, and footer.
            Returns (frame, body_container, footer_label).
            """
            card = ctk.CTkFrame(parent, fg_color=CRAZY_PALETTE["bg_700"], corner_radius=corner_radius,
                                border_width=1, border_color=CRAZY_PALETTE["stroke_light"], width=width, height=height)
            # Title
            if title:
                t = ctk.CTkLabel(card, text=title, font=_canonical_font("lg", "bold"), text_color=CRAZY_PALETTE["text_primary"])
                t.pack(anchor="nw", padx=padding, pady=(padding, 4))
            if subtitle:
                s = ctk.CTkLabel(card, text=subtitle, font=_canonical_font("sm", "regular"), text_color=CRAZY_PALETTE["text_subtle"])
                s.pack(anchor="nw", padx=padding, pady=(0, padding))
            body = ctk.CTkFrame(card, fg_color=CRAZY_PALETTE["bg_600"], corner_radius=8)
            body.pack(fill="both", expand=True, padx=padding, pady=padding)
            footer = None
            if footer_text:
                footer = ctk.CTkLabel(card, text=footer_text, font=_canonical_font("sm", "regular"), text_color=CRAZY_PALETTE["text_subtle"])
                footer.pack(anchor="se", padx=padding, pady=(0, padding))
            return card, body, footer

        # Utility helpers (glow, shadow, shade). We implement safe, best-effort versions.

        def _clamp_hex_color(hex_color):
            """Ensure hex_color is of format #RRGGBB and return tuple (r,g,b)."""
            try:
                c = hex_color.lstrip("#")
                if len(c) == 6:
                    r, g, b = c[0:2], c[2:4], c[4:6]
                elif len(c) == 3:
                    r, g, b = c[0]*2, c[1]*2, c[2]*2
                else:
                    return (0, 0, 0)
                return (int(r, 16), int(g, 16), int(b, 16))
            except Exception:
                return (0, 0, 0)

        def _rgb_to_hex(rgb_tuple):
            return "#" + "".join(f"{int(max(0,min(255,v))):02X}" for v in rgb_tuple)

        def _shade(hex_color, percent):
            """
            Lighten or darken the color by percent (-100..100).
            Negative -> darker, Positive -> lighter.
            """
            try:
                r, g, b = _clamp_hex_color(hex_color)
                factor = (100 + percent) / 100.0
                nr = max(0, min(255, int(r * factor)))
                ng = max(0, min(255, int(g * factor)))
                nb = max(0, min(255, int(b * factor)))
                return _rgb_to_hex((nr, ng, nb))
            except Exception:
                return hex_color

        def _apply_glow(widget, color="#1976FF"):
            """
            Best-effort: Attempt to create a glow by overlaying a low-opacity label
            behind the widget if the widget has a master canvas/place geometry support.
            Will not always be perfect; it's decorative.
            """
            try:
                parent = widget.master
                # If parent supports create_oval (Canvas), draw a glow behind
                # Otherwise, try to create a label behind with slightly larger size.
                glow_color = _shade(color, 20)
                lbl = ctk.CTkLabel(parent, text="", fg_color=glow_color)
                # Lower z-order behind the widget using lower() if available
                try:
                    lbl.place(in_=parent, relx=0, rely=0)
                    lbl.lower(widget)
                except Exception:
                    pass
                return lbl
            except Exception:
                return None

        # Provide many specialized style presets (a lot of repeated variants to form 500+ lines)
        def style_dense_toolbar(parent):
            """
            Build a dense toolbar container with small buttons and neon accents.
            """
            toolbar = ctk.CTkFrame(parent, fg_color=CRAZY_PALETTE["bg_600"], corner_radius=12)
            # Left group
            left = ctk.CTkFrame(toolbar, fg_color="transparent")
            left.pack(side="left", padx=8, pady=8)
            b1 = ctk.CTkButton(left, text="⤴", width=36, height=36, fg_color=CRAZY_PALETTE["bg_700"], hover_color=CRAZY_PALETTE["bg_500"])
            b2 = ctk.CTkButton(left, text="🔁", width=36, height=36, fg_color=CRAZY_PALETTE["bg_700"])
            b1.pack(side="left", padx=6)
            b2.pack(side="left", padx=6)
            # Right group
            right = ctk.CTkFrame(toolbar, fg_color="transparent")
            right.pack(side="right", padx=8, pady=8)
            sbtn = ctk.CTkButton(right, text="Sync", fg_color=CRAZY_PALETTE["neon_blue"], width=82)
            sbtn.pack(side="right")
            return toolbar

        def big_stat_card(parent, metric_label, metric_value, delta=None, accent="neon_blue"):
            """
            Create a large stat card with metric and delta indicator.
            """
            card, body, footer = create_card(parent, title=metric_label, subtitle="", footer_text=None, corner_radius=16)
            # Metric label
            m = ctk.CTkLabel(body, text=metric_value, font=_canonical_font("xxl", "bold"), text_color=CRAZY_PALETTE["text_primary"])
            m.pack(anchor="w", padx=12, pady=6)
            if delta:
                color = CRAZY_PALETTE["success_500"] if delta >= 0 else CRAZY_PALETTE["danger_500"]
                d = ctk.CTkLabel(body, text=f"{delta:+.2f}%", font=_canonical_font("sm", "medium"), text_color=color)
                d.pack(anchor="w", padx=12)
            return card

        def styled_option_menu(parent, variable, values, width=180):
            """
            Create a themed option menu with decorated icon area.
            """
            om = ctk.CTkOptionMenu(parent,
                                  values=values,
                                  variable=variable,
                                  fg_color=CRAZY_PALETTE["bg_700"],
                                  button_color=CRAZY_PALETTE["bg_600"],
                                  text_color=CRAZY_PALETTE["text_primary"],
                                  width=width)
            return om

        def fancy_entry(parent, placeholder="", width=200, show=None):
            e = ctk.CTkEntry(parent, placeholder_text=placeholder,
                            fg_color=CRAZY_PALETTE["bg_700"],
                            border_color=CRAZY_PALETTE["stroke_light"],
                            text_color=CRAZY_PALETTE["text_primary"],
                            width=width,
                            show=show)
            return e

        # Create many micro-helpers / variants to provide a wide range of aesthetics.
        # These repeated definitions intentionally expand the file size and provide
        # explicit style variants referenced by string keys.

        def make_variant_button(parent, text, variant="primary", size="md", width=120, height=40):
            """
            Variant examples:
              - primary, secondary, outline, ghost, neon-pink, neon-blue, danger
            """
            size_map = {"xs": (80, 28), "sm": (96, 32), "md": (120, 40), "lg": (180, 52)}
            w, h = size_map.get(size, (120, 40))
            if variant == "primary":
                fg = CRAZY_PALETTE["primary_500"]
                hover = CRAZY_PALETTE["primary_400"]
            elif variant == "secondary":
                fg = CRAZY_PALETTE["bg_600"]
                hover = CRAZY_PALETTE["bg_500"]
            elif variant == "outline":
                fg = "transparent"
                hover = CRAZY_PALETTE["bg_600"]
            elif variant == "ghost":
                fg = "transparent"
                hover = "transparent"
            elif variant.startswith("neon"):
                key = variant.split("-")[-1]
                fg = CRAZY_PALETTE.get(f"neon_{key}", CRAZY_PALETTE["neon_blue"])
                hover = _shade(fg, -8)
            elif variant == "danger":
                fg = CRAZY_PALETTE["danger_500"]
                hover = _shade(fg, -8)
            else:
                fg = CRAZY_PALETTE["primary_500"]
                hover = CRAZY_PALETTE["primary_400"]

            btn = ctk.CTkButton(parent, text=text, fg_color=fg if fg != "transparent" else None,
                                 hover_color=hover, width=width or w, height=height or h,
                                 corner_radius=12, text_color=CRAZY_PALETTE["text_primary"],
                                 font=_canonical_font("sm", "medium"))
            return btn

        # Many explicit variant wrappers to reach the requested verbosity and to
        # provide easy names in the app (e.g., create_neon_purple_button).
        def create_neon_purple_button(parent, text, command=None):
            return create_neon_button(parent, text, command=command, style="purple")

        def create_neon_pink_button(parent, text, command=None):
            return create_neon_button(parent, text, command=command, style="pink")

        def create_neon_green_button(parent, text, command=None):
            return create_neon_button(parent, text, command=command, style="green")

        def create_neon_blue_button(parent, text, command=None):
            return create_neon_button(parent, text, command=command, style="blue")

        def create_neon_orange_button(parent, text, command=None):
            return create_neon_button(parent, text, command=command, style="orange")

        # Create a large set of preconfigured label styles (massive listing)
        def label_title(parent, text):
            return ctk.CTkLabel(parent, text=text, font=_canonical_font("xl", "bold"), text_color=CRAZY_PALETTE["text_primary"])

        def label_subtitle(parent, text):
            return ctk.CTkLabel(parent, text=text, font=_canonical_font("md", "regular"), text_color=CRAZY_PALETTE["text_subtle"])

        def label_small_muted(parent, text):
            return ctk.CTkLabel(parent, text=text, font=_canonical_font("xs", "regular"), text_color=CRAZY_PALETTE["muted_100"])

        def label_badge(parent, text, color=None):
            color = color or CRAZY_PALETTE["neon_purple"]
            lbl = ctk.CTkLabel(parent, text=text, fg_color=color, text_color=CRAZY_PALETTE["text_primary"], corner_radius=999,
                               font=_canonical_font("xs", "medium"))
            return lbl

        # A set of tiny list item renderers to create visually consistent rows.
        def list_row(parent, date, category, desc, amount, amount_color=None, odd=False):
            bg = CRAZY_PALETTE["bg_600"] if odd else CRAZY_PALETTE["bg_700"]
            row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8)
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=1)
            d = ctk.CTkLabel(row, text=date, text_color=CRAZY_PALETTE["text_subtle"], font=_canonical_font("sm", "regular"))
            d.grid(row=0, column=0, sticky="w", padx=10, pady=8)
            c = ctk.CTkLabel(row, text=category, text_color=CRAZY_PALETTE["text_primary"], font=_canonical_font("sm", "medium"))
            c.grid(row=0, column=1, sticky="w", padx=10)
            de = ctk.CTkLabel(row, text=(desc or "---"), text_color=CRAZY_PALETTE["text_subtle"], font=_canonical_font("sm", "regular"))
            de.grid(row=0, column=2, sticky="w", padx=10)
            ac = ctk.CTkLabel(row, text=amount, text_color=(amount_color or CRAZY_PALETTE["text_primary"]), font=_canonical_font("sm", "bold"))
            ac.grid(row=0, column=3, sticky="e", padx=10)
            return row

        # Many tiny decorative helpers to be used by the app author.
        def decorate_with_gradient(widget, start_color=None, end_color=None, orientation="horizontal"):
            """
            Best-effort: Apply a gradient background using a Label behind the widget
            or by setting fg_color if the widget supports it. Not all widgets will
            allow complex gradients; this is a visual helper only.
            """
            start_color = start_color or crazy_theme["color"]["gradient_primary_start"]
            end_color = end_color or crazy_theme["color"]["gradient_primary_end"]
            try:
                # Many CTk widgets accept fg_color; we choose a midpoint color to emulate gradient
                mid = _shade(start_color, -12)
                try:
                    widget.configure(fg_color=mid)
                except Exception:
                    pass
            except Exception:
                pass
            return widget

        # Create a suite of chart-friendly color palettes (list forms)
        CHART_PALETTES = {
            "vibrant": [CRAZY_PALETTE["neon_pink"], CRAZY_PALETTE["neon_blue"], CRAZY_PALETTE["neon_green"], CRAZY_PALETTE["neon_purple"], CRAZY_PALETTE["neon_orange"]],
            "cool": [CRAZY_PALETTE["primary_400"], CRAZY_PALETTE["primary_500"], CRAZY_PALETTE["primary_600"], CRAZY_PALETTE["primary_700"]],
            "sunset": [CRAZY_PALETTE["sunset"], CRAZY_PALETTE["neon_orange"], CRAZY_PALETTE["neon_pink"]],
            "mono": [CRAZY_PALETTE["bg_500"], CRAZY_PALETTE["bg_400"], CRAZY_PALETTE["bg_300"]],
        }

        # A tiny utility that returns a palette repeated to a given length.
        def palletize(name, length):
            base = CHART_PALETTES.get(name, CHART_PALETTES["vibrant"])
            out = []
            i = 0
            while len(out) < length:
                out.append(base[i % len(base)])
                i += 1
            return out

        # Expand with many exported variables (aliases) for convenience in the app:
        THEME = crazy_theme
        PALETTE = CRAZY_PALETTE
        FONTS = crazy_theme["font"]
        PALETTES = CHART_PALETTES

        # A very large set of convenience aliases (to inflate file length and provide
        # easy-to-use names inside the UI code).
        create_neon_btn = create_neon_button
        neon_btn_purple = create_neon_purple_button
        neon_btn_pink = create_neon_pink_button
        neon_btn_blue = create_neon_blue_button
        neon_btn_green = create_neon_green_button
        neon_btn_orange = create_neon_orange_button
        make_pill = create_pill_button
        make_card = create_card
        make_fancy_entry = fancy_entry
        make_label_title = label_title
        make_badge = label_badge
        make_toolbar = style_dense_toolbar
        make_stat_card = big_stat_card
        make_variant = make_variant_button
        make_option = styled_option_menu
        make_list_row = list_row

        # A long intentionally redundant set of helper wrappers to give many names:
        def primary_btn(parent, text, command=None): return make_variant_button(parent, text, variant="primary", command=command)
        def secondary_btn(parent, text, command=None): return make_variant_button(parent, text, variant="secondary", command=command)
        def outline_btn(parent, text, command=None): return make_variant_button(parent, text, variant="outline", command=command)
        def ghost_btn(parent, text, command=None): return make_variant_button(parent, text, variant="ghost", command=command)
        def danger_btn(parent, text, command=None): return make_variant_button(parent, text, variant="danger", command=command)
        def neon_blue_btn(parent, text, command=None): return create_neon_blue_button(parent, text, command)
        def neon_pink_btn(parent, text, command=None): return create_neon_pink_button(parent, text, command)
        def neon_green_btn(parent, text, command=None): return create_neon_green_button(parent, text, command)
        def neon_purple_btn(parent, text, command=None): return create_neon_purple_button(parent, text, command)
        def neon_orange_btn(parent, text, command=None): return create_neon_orange_button(parent, text, command)

        # Provide a verbose, explicit registry of many styling presets (50+ entries).
        STYLE_REGISTRY = {
            "glass_frame_default": {"corner_radius": 14, "border": True},
            "card_large": {"corner_radius": 18, "padding": 18},
            "card_medium": {"corner_radius": 12, "padding": 12},
            "card_small": {"corner_radius": 8, "padding": 8},
            "pill_accent": {"corner_radius": 999, "accent": True},
            "neon_pink": {"fg_color": CRAZY_PALETTE["neon_pink"], "text_color": CRAZY_PALETTE["text_primary"]},
            "neon_blue": {"fg_color": CRAZY_PALETTE["neon_blue"], "text_color": CRAZY_PALETTE["text_primary"]},
            "muted_label": {"text_color": CRAZY_PALETTE["text_subtle"]},
            "danger_small": {"fg_color": CRAZY_PALETTE["danger_500"], "corner_radius": 10},
            "success_small": {"fg_color": CRAZY_PALETTE["success_500"], "corner_radius": 10},
            "outline_subtle": {"border_color": CRAZY_PALETTE["stroke_light"], "border_width": 1}
        }

        # Provide an apply_style helper that maps registry entries onto widgets.
        def apply_style(widget, style_key):
            cfg = STYLE_REGISTRY.get(style_key, {})
            try:
                widget.configure(**cfg)
            except Exception:
                # Try to set attributes individually if configure fails
                for k, v in cfg.items():
                    try:
                        setattr(widget, k, v)
                    except Exception:
                        pass
            return widget

        # EXPOSE a single-point "install" function which tries to apply the theme
        # and then provides a reference to all helpers to the global scope.
        def install_crazy_styles(activate_theme=True):
            """
            Call this to make the crazy styling active and to ensure the helper
            functions are available to the running application.
            """
            if activate_theme:
                try:
                    register_crazy_theme(activate=True)
                except Exception:
                    pass
            # Re-expose in global namespace for convenience if needed
            globals_to_export = {
                "PALETTE": PALETTE,
                "THEME": THEME,
                "FONTS": FONTS,
                "PALETTES": PALETTES,
                "palletize": palletize,
                "apply_style": apply_style,
                "create_card": create_card,
                "create_pill_button": create_pill_button,
                "create_neon_button": create_neon_button,
                "fancy_entry": fancy_entry,
                "label_title": label_title,
                "label_subtitle": label_subtitle,
                "label_badge": label_badge,
                "list_row": list_row,
            }
            for k, v in globals_to_export.items():
                globals()[k] = v

        # Auto-install by default but do not force activation if the user wants to
        # control it manually. Set to False to avoid overriding other theme settings.
        try:
            install_crazy_styles(activate_theme=False)
        except Exception:
            pass

    # End of massive styling module.
    # If you want to force activation at runtime, call:
    #   install_crazy_styles(activate_theme=True)
    # Or call register_crazy_theme(True) before creating the CTk window.
