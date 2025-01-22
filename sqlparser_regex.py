import re
import pandas as pd

def extract_table_aliases(sql_query):
    """Extract table names and their aliases from FROM and JOIN clauses."""
    # Fix regex to capture aliases correctly
    table_pattern = re.compile(r'\bFROM\s+([\w.]+)\s+(\w+)?', re.IGNORECASE)
    join_pattern = re.compile(r'\b(JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN)\s+([\w.]+)\s+(\w+)?', re.IGNORECASE)

    tables = {}

    # Extract FROM clause tables
    for match in table_pattern.findall(sql_query):
        print("[DEBUG] FROM Match:", match)
        table_name, alias = match
        if alias:  
            tables[alias] = table_name  # Correctly store alias -> table
        else:
            tables[table_name] = table_name  # Store full table name if no alias

    # Extract JOIN clause tables
    for match in join_pattern.findall(sql_query):
        print("[DEBUG] JOIN Match:", match)
        _, table_name, alias = match
        if alias:
            tables[alias] = table_name  # Store alias
        else:
            tables[table_name] = table_name  # Store table itself

    print("\n[DEBUG] Corrected Table Aliases Mapping:")
    for alias, table in tables.items():
        print(f"  - Alias: {alias} -> Table: {table}")
    print(tables)

    return tables

def extract_columns(sql_query, table_aliases):
    """Extract column names and their associated table aliases. Non-greedy approach so it matches to the first FROM."""
    select_pattern = re.compile(r'\bSELECT\s+(.*?)\bFROM\b', re.IGNORECASE | re.DOTALL)
    column_list = []

    # Find the SELECT clause
    select_match = select_pattern.search(sql_query)
    if not select_match:
        return []

    select_clause = select_match.group(1)
    print(f"\n[DEBUG] Extracted SELECT Clause: {select_clause.strip()}")

    # Extract columns including functions (SUM, COUNT, etc.)
    column_pattern = re.compile(r'([\w.()]+)\s*(?:AS\s+(\w+))?', re.IGNORECASE)
    for column_match in column_pattern.findall(select_clause):
        column, alias = column_match
        column = column.strip()

        # Handle aggregate functions (SUM, COUNT, etc.)
        if "(" in column and ")" in column:
            func_match = re.search(r'(\w+)\(([\w.]+)\)', column)
            if func_match:
                function_name, column_ref = func_match.groups()
                table_alias, column_name = (column_ref.split('.') if '.' in column_ref else (None, column_ref))
                actual_table = table_aliases.get(table_alias, table_alias)

                print(f"[DEBUG] Function Found: {function_name}({column_name}) under {actual_table} ({table_alias})")
                column_list.append((actual_table, table_alias, f"{function_name}({column_name})"))
                continue

        # Standard column extraction
        table_alias, column_name = (column.split('.') if '.' in column else (None, column))
        actual_table = table_aliases.get(table_alias, table_alias)

        print(f"[DEBUG] Extracted Column: {column_name} under {actual_table} ({table_alias})")
        column_list.append((actual_table, table_alias, column_name))

    return column_list

def save_to_excel(data, filename="sql_parsed_fixed.xlsx"):
    """Save extracted SQL metadata to an Excel file."""
    df = pd.DataFrame(data, columns=["Table Name", "Alias", "Column Name"])
    df.to_excel(filename, index=False)
    print(f"\n[INFO] Data successfully saved to {filename}")

# Example SQL Query Handling Aliases, Functions, and Parentheses
sql_query = """
SELECT f.port_number, SUM(t.amount) AS total_amount, p.product_name
FROM portfolios f
JOIN transactions t ON f.portfolio_id = t.portfolio_id
LEFT JOIN products p ON t.product_id = p.product_id
WHERE f.port_number > 100
UNION ALL
SELECT f2.port_number, SUM(t2.amount) AS total_amount, p2.product_name
FROM portfolios f2
JOIN transactions t2 ON f2.portfolio_id = t2.portfolio_id
LEFT JOIN products p2 ON t2.product_id = p2.product_id
"""

# Extract Table and Alias Mapping
table_aliases = extract_table_aliases(sql_query)

# Extract Column Information
parsed_data = extract_columns(sql_query, table_aliases)

# **Fix: Replace Aliases with Actual Table Names**
final_parsed_data = [
    (table_aliases.get(alias, alias), alias, column_name)
    for table, alias, column_name in parsed_data
]

print("\n[DEBUG] Final Parsed Data (Table, Alias, Column):")
for row in final_parsed_data:
    print(f"  - {row}")

# Save the corrected data to an Excel file
save_to_excel(final_parsed_data, "sql_parsed_final_fixed.xlsx")
