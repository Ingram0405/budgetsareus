
import sqlite3  # Importing SQLite3
from colorama import Fore, init
init(autoreset=True)


def letsbudget():
    """
    This is the main function that starts the Budgets Are Us program.

    It does the following:
    - Connects to the SQLite database (creates it if it doesn't exist).
    - Enables foreign key constraints so linked data works properly.
    - Creates all the tables we need for the app.
    - Displays the menu and runs in a loop until the user chooses to quit.
    """
    connect = sqlite3.connect('budgets_are_us.db')
    budgets = connect.cursor()
    budgets.execute("PRAGMA foreign_keys = ON")
    create_tables(budgets)


    while True:
    # Here we present the menu to the user: 
        menu = input('''\nSelect one of the following options:
1 - Add Expense
2 - View Expenses
3 - View Expenses by Category
4 - Add Income
5 - View Income
6 - View Income by Category
7 - Set Budget for a Category
8 - View Budget for a Category
9 - Set Financial Goals
10 - View Progress Towards Financial Goals
11 - Quit\n
: ''').strip()

        if menu == '1':
            add_expense(budgets, connect)

        elif menu == '2':
            view_expenses(budgets)

        elif menu == '3':
            view_by_category(budgets)

        elif menu == '4':
            add_income(budgets, connect)

        elif menu == '5':
            view_income(budgets)

        elif menu == '6':
            view_income_category(budgets)

        elif menu == '7':
            set_budget(budgets, connect)

        elif menu == '8':
            view_budget(budgets)

        elif menu == '9':
            set_financial_goal(budgets, connect)

        elif menu == '10':
            view_financial_goals(budgets, connect)

        elif menu == '11':
            print(Fore.CYAN + 'Goodbye from Budgets Are Us! 💸')
            break

        else:
            print("You have entered an invalid number. Please try again")


    connect.commit()
    connect.close()

def create_tables(budgets):
    """
    This function sets up all the necessary tables in the database 
    if they don’t already exist.

    It creates the following tables:
    - expense_categories: list of unique categories for expenses
    - income_categories: list of unique categories for income
    - expenses: to store expense transactions
    - income: to store income transactions
    - budget: stores budget amounts for each expense category
    - financial_goals: lets users track their savings or financial targets

    It uses the cursor passed from the main function to run the SQL commands.
    """

    budgets.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')


    budgets.execute('''
        CREATE TABLE IF NOT EXISTS income_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')


    budgets.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT DEFAULT CURRENT_DATE,
            note TEXT,
            FOREIGN KEY (category) REFERENCES expense_categories(name)
        )
    ''')


    budgets.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT DEFAULT CURRENT_DATE,
            note TEXT,
            FOREIGN KEY (category) REFERENCES income_categories(name)
        )
    ''')


    budgets.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            budget_amount REAL NOT NULL,
            FOREIGN KEY (category) REFERENCES expense_categories(name)
        )
    ''')



    budgets.execute('''
        CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_progress REAL DEFAULT 0.0
        )
    ''')


# Default Data for Expenses
    budgets.execute("""
        INSERT OR IGNORE INTO expense_categories (name) 
        VALUES ('Food'), ('Transport'), ('Utilities'), 
        ('Entertainment'), ('Health')
        """)

    #  Default Data for Income
    budgets.execute("""
        INSERT OR IGNORE INTO income_categories (name) 
        VALUES ('Salary'), ('Freelance'), ('Investment'), 
        ('Bonus'), ('Other')
    """)


#  Menu Option 1 – Add Expense
def add_expense(budgets, connect):
    """
    - Allows the user to add or manage expenses.
    - Users can:
      * View and select existing categories
      * Add a new category
      * Delete a category
      * Update the most recent expense
      * Add a new expense entry
    """
    print(Fore.CYAN + "\n📂 Expense Categories:")
    budgets.execute("SELECT name FROM expense_categories")
    categories = budgets.fetchall()

    if categories:
        for i, category in enumerate(categories, start=1):
            print(f"{i}. {category[0]}")
    else:
        print(Fore.LIGHTWHITE_EX + "⚠️  No categories found yet.")

    # Ask user for action
    selection = input(
        Fore.LIGHTWHITE_EX + "\nEnter the number of a category,\n"
        "or type 'new' to add, 'delete' to remove one,\n"
        "or 'update' to modify last expense: "
    ).strip().lower()

    # Option to add new category
    if selection == 'new':
        new_category = input("Enter the new category name: ").strip().title()

        if not new_category:
            print(Fore.RED + "❌ Category name cannot be empty.")
            return

        try:
            budgets.execute(
                "INSERT INTO expense_categories (name) "
                "VALUES (?)", (new_category,)
            )
            connect.commit()
            print(Fore.GREEN + f"✅ New category '{new_category}' added.")
        except sqlite3.IntegrityError:
            print(Fore.RED + "❌ That category already exists.")
        return

    # Option to delete a category
    elif selection == 'delete':
        del_index = input("Enter the number of the category to " \
                          "delete: ").strip()
        try:
            del_index = int(del_index)
            if 1 <= del_index <= len(categories):
                category = categories[del_index - 1][0]

                confirm = input(
                    Fore.RED + f"⚠️  Are you sure you want to "
                               f"delete '{category}'? "
                               "This cannot be undone. "
                               "(y/n): ").strip().lower()
                if confirm == 'y':
                    budgets.execute(
                        "DELETE FROM expense_categories WHERE "
                        "name = ?", (category,)
                    )
                    budgets.execute(
                        "DELETE FROM expenses WHERE category = ?", (category,)
                    )
                    connect.commit()
                    print(Fore.GREEN + f"🗑️ Category '{category}' "
                                       f"and its expenses deleted.")
                else:
                    print(Fore.YELLOW + "Deletion cancelled.")
            else:
                print(Fore.RED + "❌ Invalid category number.")
        except ValueError:
            print(Fore.RED + "❌ Please enter a valid number.")
        return

    # Option to update most recent expense
    elif selection == 'update':
        budgets.execute("SELECT id, category, amount FROM expenses " \
                        "ORDER BY date DESC LIMIT 1")
        last = budgets.fetchone()

        if not last:
            print(Fore.YELLOW + "⚠️ No expense records found.")
            return

        print(Fore.LIGHTMAGENTA_EX + f"\nLast recorded: "
                                     f"{last[1]} | R{last[2]:.2f}")
        try:
            new_amount = float(input("Enter new amount: ").strip())
            budgets.execute("UPDATE expenses SET amount = ? "
                            "WHERE id = ?", (new_amount, last[0]))
            connect.commit()
            print(Fore.GREEN + f"✅ Expense updated to R{new_amount:.2f}.")
        except ValueError:
            print(Fore.RED + "❌ Please enter a valid number.")
        return

    # Add a new expense
    else:
        try:
            index = int(selection)
            if 1 <= index <= len(categories):
                category = categories[index - 1][0]
            else:
                print(Fore.RED + "❌ Invalid category number.")
                return
        except ValueError:
            print(Fore.RED + "❌ Invalid input. Enter a number, 'new', "
                             "'delete', or 'update'.")
            return

        try:
            amount = float(input("Enter the amount spent "
                                 "(e.g., 45.50): ").strip())
        except ValueError:
            print(Fore.RED + "❌ Amount must be a valid number.")
            return

        budgets.execute(
            "INSERT INTO expenses (category, amount) VALUES (?, ?)",
            (category, amount)
        )
        connect.commit()

        print(Fore.GREEN + f"✅ Expense of R{amount:.2f} "
                           f"added under '{category}'.")


#  Menu Item 2, View Expense
def view_expenses(budgets):
    """
    Displays all expenses stored in the database.
    Shows date, category, and amount.
    """
    budgets.execute("SELECT date, category, amount FROM expenses ORDER " \
                    "BY date DESC")
    records = budgets.fetchall()

    if not records:
        print(Fore.LIGHTWHITE_EX + "\nNo expenses recorded yet.")
        return

    print(Fore.CYAN + "\n📄 Your Expenses:\n" + "-"*40)
    for row in records:
        date, category, amount = row
        print(f"🗓️  {date} | 📂 {category} | 💰 R{amount:.2f}")


    #  Menu Item 3 – View Expenses by Category
def view_by_category(budgets):
    """
    - Shows all expenses grouped by category.
    - Displays category, date, and amount in a clean format.
    """
    budgets.execute("SELECT category, date, amount FROM expenses " \
                    "ORDER BY category, date DESC")
    records = budgets.fetchall()

    if not records:
        print(Fore.LIGHTWHITE_EX + "\n⚠ No expenses found.")
        return

    print(Fore.CYAN + "\n🗂 Expenses by Category\n" + "="*42)

    current_category = None
    for category, date, amount in records:
        if category != current_category:
            current_category = category
            print(Fore.LIGHTMAGENTA_EX + f"\n📁 {category}")
        print(Fore.WHITE + f"   🕓 {date}  |  💵 R{amount:.2f}")


# Menu Item 4 – Add Income
def add_income(budgets, connect):
    """
    - Allows the user to add a new income record.
    - Displays current income categories from the database.
    - Lets the user select one or type 'new' to add a new category.
    - Prompts for the income amount.
    - Inserts the income (and category, if new) into the database.
    """

    print(Fore.CYAN + "\n🧾 Income Categories:")
    budgets.execute("SELECT name FROM income_categories")
    categories = budgets.fetchall()

    if categories:
        for i, category in enumerate(categories, start=1):
            print(f"{i}. {category[0]}")
    else:
        print(Fore.LIGHTWHITE_EX + "⚠️  No categories found yet.")

    selection = input(
        Fore.LIGHTWHITE_EX + "\nEnter the number of a category, or "
                             "type 'new' to add one: "
    ).strip()

    if selection.lower() == 'new':
        new_category = input("Enter the new income category "
                             "name: ").strip().title()

        if not new_category:
            print(Fore.RED + "❌ Category name cannot be empty.")
            return

        try:
            budgets.execute(
                "INSERT INTO income_categories (name) VALUES "
                "(?)", (new_category,)
            )
            connect.commit()
            category = new_category
            print(Fore.GREEN + f"🟢 New category '{category}' added.")
        except sqlite3.IntegrityError:
            print(Fore.RED + "❌ That category already exists.")
            return
    else:
        try:
            index = int(selection)
            if 1 <= index <= len(categories):
                category = categories[index - 1][0]
            else:
                print(Fore.RED + "❌ Invalid category number.")
                return
        except ValueError:
            print(Fore.RED + "❌ Invalid input. Please enter a "
                             "number or 'new'.")
            return

    try:
        amount = float(input("Enter the income amount "
                             "(e.g., 3000.00): ").strip())
    except ValueError:
        print(Fore.RED + "❌ Amount must be a valid number.")
        return

    budgets.execute(
        "INSERT INTO income (category, amount) VALUES (?, ?)",
        (category, amount)
    )
    connect.commit()

    print(Fore.GREEN + f"Income of R{amount:.2f} "
                       f"added under '{category}'.")


# Menu Option 5 – View Income
def view_income(budgets):
    """
    Displays all income entries stored in the database.
    Shows date, category, and amount.
    """
    budgets.execute("SELECT date, category, amount FROM income " \
                    "ORDER BY date DESC")
    records = budgets.fetchall()

    if not records:
        print(Fore.LIGHTYELLOW_EX + "\n⚠ No income records found.")
        return

    print(Fore.CYAN + "\n📑 Income Records:\n" + "-"*40)
    for row in records:
        date, category, amount = row
        print(f"🗓 {date} | 🗃 {category} | 🪙 R{amount:.2f}")


   # Menu Option 6 – View Income by Category
def view_income_category(budgets):
    """
    - Shows all income entries grouped by category.
    - Displays category, date, and amount.
    """
    budgets.execute("SELECT category, date, amount FROM income ORDER " \
                    "BY category, date DESC")
    records = budgets.fetchall()

    if not records:
        print(Fore.LIGHTWHITE_EX + "\n⚠ No income records found.")
        return

    print(Fore.CYAN + "\n📚 Income by Category\n" + "=" * 42)

    current_category = None
    for category, date, amount in records:
        if category != current_category:
            current_category = category
            print(Fore.LIGHTMAGENTA_EX + f"\n🗂 {category}")
        print(Fore.WHITE + f"   🗓 {date}  |  💹 R{amount:.2f}")


  # Menu Option 7 – Set Budget for a Category
def set_budget(budgets, connect):
    """
    - Allows the user to set a budget for an expense category.
    - Displays all current categories and lets the user select or add one.
    - Prompts for a budget amount.
    - Updates or inserts the budget into the database.
    """
    print(Fore.CYAN + "\n🧾 Set Budget for a Category")

    budgets.execute("SELECT name FROM expense_categories")
    categories = budgets.fetchall()

    if categories:
        for i, category in enumerate(categories, start=1):
            print(f"{i}. {category[0]}")
    else:
        print(Fore.LIGHTWHITE_EX + "⚠️  No categories found.")

    selection = input(
        Fore.LIGHTWHITE_EX + "\nEnter the number of a category, "
                             "or type 'new' to add one: "
    ).strip()

    if selection.lower() == 'new':
        new_category = input("Enter the new category " \
                             "name: ").strip().title()

        if not new_category:
            print(Fore.RED + "❌ Category name cannot be empty.")
            return

        try:
            budgets.execute(
                "INSERT INTO expense_categories (name) "
                "VALUES (?)", (new_category,)
            )
            connect.commit()
            category = new_category
            print(Fore.GREEN + f"✅ New category '{category}' added.")
        except sqlite3.IntegrityError:
            print(Fore.RED + "❌ That category already exists.")
            return
    else:
        try:
            index = int(selection)
            if 1 <= index <= len(categories):
                category = categories[index - 1][0]
            else:
                print(Fore.RED + "❌ Invalid category number.")
                return
        except ValueError:
            print(Fore.RED + "❌ Invalid input. Please enter a "
                             "number or 'new'.")
            return

    try:
        amount = float(input("Enter the monthly budget amount "
                             "(e.g., 1200.00): ").strip())
    except ValueError:
        print(Fore.RED + "❌ Amount must be a valid number.")
        return

    budgets.execute(
        "INSERT INTO budget (category, budget_amount) VALUES (?, ?) "
        "ON CONFLICT(category) DO UPDATE SET budget_amount = " \
        "excluded.budget_amount",
        (category, amount)
    )
    connect.commit()

    print(Fore.GREEN + f"📌 Budget of R{amount:.2f} set "
                       f"for '{category}'.")
    

# Menu Option 8 – View Budget for a Category
def view_budget(budgets):
    """
    Displays the monthly budget set for each expense category.
    Also shows total spending so far in that category and remaining budget.
    """
    budgets.execute('''
        SELECT b.category, b.budget_amount,
               IFNULL(SUM(e.amount), 0) AS total_spent
        FROM budget b
        LEFT JOIN expenses e ON b.category = e.category
        GROUP BY b.category, b.budget_amount
    ''')
    rows = budgets.fetchall()

    if not rows:
        print(Fore.LIGHTWHITE_EX + "\n⚠ No budgets have been set yet.")
        return

    print(Fore.CYAN + "\n📊 Budget Overview\n" + "-"*42)
    for category, budget_amount, total_spent in rows:
        remaining = budget_amount - total_spent

        print(Fore.LIGHTMAGENTA_EX + f"\n📁 {category}")
        print(Fore.WHITE + f"   💰 Budget:     R{budget_amount:.2f}")
        print(f"   💸 Spent:      R{total_spent:.2f}")
        if remaining >= 0:
            print(Fore.GREEN + f"   ✅ Remaining:  R{remaining:.2f}")
        else:
            print(Fore.RED + f"   🔴 Over by:    R{abs(remaining):.2f}")


# Menu Option 9 – Set Financial Goals
def set_financial_goal(budgets, connect):
    """
    Replaces any existing goal with a new one.
    Only one active financial goal is stored.
    """
    print(Fore.CYAN + "\n🎯 Set Your Single Financial Goal")

    description = input(Fore.LIGHTWHITE_EX + "Enter your goal description: ").strip().title()
    if not description:
        print(Fore.RED + "❌ Goal description cannot be empty.")
        return

    try:
        target = float(input("Enter your savings target (e.g., 5000.00): ").strip())
        if target <= 0:
            print(Fore.RED + "❌ Target must be positive.")
            return
    except ValueError:
        print(Fore.RED + "❌ Invalid number.")
        return

    budgets.execute("DELETE FROM financial_goals")

    # Add new goal
    budgets.execute('''
        INSERT INTO financial_goals (description, target_amount, current_progress)
        VALUES (?, ?, 0)
    ''', (description, target))
    connect.commit()

    print(Fore.GREEN + f"✅ Goal '{description}' set with target R{target:.2f}.")


# Menu Option 10 – View Progress Towards Financial Goals
def view_financial_goals(budgets, connect):
    """
    Shows the active goal and calculates live savings progress:
    Net Savings = Total Income - Total Expenses
    """
    budgets.execute("SELECT description, target_amount FROM financial_goals")
    goal = budgets.fetchone()

    if not goal:
        print(Fore.LIGHTWHITE_EX + "\n⚠ No financial goal set.")
        return

    description, target = goal

    budgets.execute("SELECT IFNULL(SUM(amount), 0) FROM income")
    total_income = budgets.fetchone()[0]

    budgets.execute("SELECT IFNULL(SUM(amount), 0) FROM expenses")
    total_expenses = budgets.fetchone()[0]

    savings = total_income - total_expenses
    percent = (savings / target) * 100 if target > 0 else 0
    emoji = "🎯" if percent >= 100 else "📈" if percent >= 50 else "⚠️"

    print(Fore.CYAN + "\n📈 Financial Goal Progress\n" + "-"*42)
    print(Fore.LIGHTMAGENTA_EX + f"\n🎯 {description}")
    print(Fore.WHITE +
          f"   Target:   R{target:.2f}\n"
          f"   Saved:    R{savings:.2f}\n"
          f"   Progress: {percent:.1f}% {emoji}")


if __name__ == "__main__":
    letsbudget()
