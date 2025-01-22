import sqlparse
import pandas as pd

def extract_sql_info_fixed(sql_query):
    parsed = sqlparse.parse(sql_query)
    all_columns = []
    
    for statement in parsed:
        if not statement.get_type() == "SELECT":
            continue

        tables, aliases = extract_tables(statement)
        columns = extract_columns(statement, aliases)

        for col, table_alias in columns:
            table_name = aliases.get(table_alias, table_alias)  # Resolve table name
            if table_name:  # Avoid empty rows
                all_columns.append((table_name, table_alias, col))

    return all_columns

def extract_tables(statement):
    """ Extracts tables and their aliases """
    tables = {}
    from_seen = False

    for token in statement.tokens:
        if token.value.upper() == "FROM":
            from_seen = True
            continue

        if from_seen:
            if isinstance(token, sqlparse.sql.IdentifierList):
                for identifier in token.get_identifiers():
                    table, alias = extract_table_alias(identifier)
                    tables[alias or table] = table
            elif isinstance(token, sqlparse.sql.Identifier):
                table, alias = extract_table_alias(token)
                tables[alias or table] = table
            elif token.value.upper() in ["JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN"]:
                continue  # Skip join keywords

    return tables, tables.copy()  # Return table mappings

def extract_columns(statement, table_aliases):
    """ Extracts column names and their associated table aliases """
    columns = []

    for token in statement.tokens:
        if isinstance(token, sqlparse.sql.IdentifierList):
            for identifier in token.get_identifiers():
                column, alias = extract_column_alias(identifier, table_aliases)
                if column:
                    columns.append((column, alias))
        elif isinstance(token, sqlparse.sql.Identifier):
            column, alias = extract_column_alias(token, table_aliases)
            if column:
                columns.append((column, alias))
        elif isinstance(token, sqlparse.sql.Function):
            column, alias = extract_function_alias(token, table_aliases)
            if column:
                columns.append((column, alias))

    return columns

def extract_table_alias(identifier):
    """ Extracts table name and alias from an identifier """
    parts = identifier.value.split()
    if len(parts) == 1:
        return parts[0], None  # No alias
    elif len(parts) > 1:
        return parts[0], parts[-1]  # Table name and alias
    return None, None

def extract_column_alias(identifier, table_aliases):
    """ Extracts column name and its associated table alias if present """
    value = identifier.value

    # Handle cases like "SUM(amount) AS total_amount"
    if " AS " in value.upper():
        value = value.split(" AS ")[0]

    if "." in value:
        parts = value.split(".")
        table_alias = parts[0]  # Table alias
        column_name = parts[-1]  # Column name
        return column_name, table_alias

    return value, None

def extract_function_alias(token, table_aliases):
    """ Handles SQL functions like SUM(amount) AS total_amount """
    column_name = token.get_real_name() or token.get_alias()
    alias = token.get_alias()

    if column_name:
        return column_name, alias
    return str(token), None

def save_to_excel(data, filename="sql_parsed.xlsx"):
    """ Saves extracted data to an Excel file """
    df = pd.DataFrame(data, columns=["Table Name", "Alias", "Column Name"])
    df.to_excel(filename, index=False)
    print(f"Data successfully saved to {filename}")

# Example SQL Query Handling Aliases & Parentheses
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

# Extract information using the fixed version
parsed_data_fixed = extract_sql_info_fixed(sql_query)

# Save the new fixed version to an Excel file
fixed_file_path = "sql_parsed_fixed.xlsx"
df_fixed = pd.DataFrame(parsed_data_fixed, columns=["Table Name", "Alias", "Column Name"])
df_fixed.to_excel(fixed_file_path, index=False)

print(f"Fixed data saved to {fixed_file_path}")
