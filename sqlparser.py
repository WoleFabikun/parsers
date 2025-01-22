import sqlparse
import pandas as pd

def extract_sql_info(sql_query):
    parsed = sqlparse.parse(sql_query)
    columns = []
    tables = {}

    for statement in parsed:
        if not statement.get_type() == "SELECT":
            continue

        tokens = statement.tokens
        from_seen = False
        alias_map = {}

        for i, token in enumerate(tokens):
            if token.value.upper() == "FROM":
                from_seen = True
                continue
            
            if from_seen:
                # Extract tables and aliases, including JOIN clauses
                if isinstance(token, sqlparse.sql.IdentifierList):
                    for identifier in token.get_identifiers():
                        table_name, alias = extract_table_alias(identifier)
                        if table_name:
                            alias_map[alias or table_name] = table_name
                
                elif isinstance(token, sqlparse.sql.Identifier):
                    table_name, alias = extract_table_alias(token)
                    if table_name:
                        alias_map[alias or table_name] = table_name

                elif isinstance(token, sqlparse.sql.Token) and token.value.upper() in ["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"]:
                    # Look ahead to get the table being joined
                    next_token = tokens[i + 1] if i + 1 < len(tokens) else None
                    if isinstance(next_token, sqlparse.sql.Identifier):
                        table_name, alias = extract_table_alias(next_token)
                        if table_name:
                            alias_map[alias or table_name] = table_name

        tables.update(alias_map)

        # Extract column names
        for token in statement.tokens:
            if isinstance(token, sqlparse.sql.IdentifierList):
                for identifier in token.get_identifiers():
                    column_name, table_alias = extract_column_alias(identifier)
                    if column_name:
                        actual_table = tables.get(table_alias, table_alias)
                        columns.append((actual_table, table_alias, column_name))

            elif isinstance(token, sqlparse.sql.Identifier):
                column_name, table_alias = extract_column_alias(token)
                if column_name:
                    actual_table = tables.get(table_alias, table_alias)
                    columns.append((actual_table, table_alias, column_name))

    return columns

def extract_table_alias(identifier):
    """ Extracts table name and alias from an identifier """
    tokens = identifier.value.split()
    if len(tokens) == 1:
        return tokens[0], None  # No alias
    elif len(tokens) > 1:
        return tokens[0], tokens[-1]  # Table name and alias

    return None, None

def extract_column_alias(identifier):
    """ Extracts column name and its associated table alias if present """
    if "." in identifier.value:
        parts = identifier.value.split(".")
        return parts[-1], parts[0]  # column_name, table_alias
    return identifier.value, None

def save_to_excel(data, filename="sql_parsed.xlsx"):
    """ Saves extracted data to an Excel file """
    df = pd.DataFrame(data, columns=["Table Name", "Alias", "Column Name"])
    df.to_excel(filename, index=False)
    print(f"Data successfully saved to {filename}")

# Example SQL Query with JOINs
sql_query = """
SELECT c.customer_id, c.name, o.order_id, o.date, p.product_name
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN products p ON o.product_id = p.product_id
"""

# Extract information and save to Excel
parsed_data = extract_sql_info(sql_query)
save_to_excel(parsed_data)
