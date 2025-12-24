"""
Database Setup Script
This script will execute the DDL commands to create all necessary tables
"""
from database import get_db_connection
import os

def run_ddl_script():
    """Execute the DDL script to create all database tables"""

    print("=" * 70)
    print("DATABASE SETUP - Creating Tables")
    print("=" * 70)
    print()

    # Read the DDL file
    ddl_file_path = os.path.join('backend', 'Database_DDl.sql')

    if not os.path.exists(ddl_file_path):
        print(f"❌ ERROR: DDL file not found at {ddl_file_path}")
        return False

    print(f"📄 Reading DDL file: {ddl_file_path}")

    with open(ddl_file_path, 'r', encoding='utf-8') as f:
        ddl_content = f.read()

    print("✅ DDL file loaded")
    print()

    # Connect to database
    print("🔌 Connecting to database...")
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("✅ Connected successfully")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    # Split the DDL into individual statements
    # We need to handle DELIMITER changes for triggers
    statements = []
    current_statement = []
    in_delimiter_block = False
    custom_delimiter = ';'

    for line in ddl_content.split('\n'):
        line_stripped = line.strip()

        # Skip comments and empty lines
        if line_stripped.startswith('--') or not line_stripped:
            continue

        # Handle DELIMITER commands
        if line_stripped.startswith('DELIMITER'):
            if 'DELIMITER ;' in line_stripped:
                custom_delimiter = ';'
                in_delimiter_block = False
            else:
                custom_delimiter = '//'
                in_delimiter_block = True
            continue

        current_statement.append(line)

        # Check for statement end
        if in_delimiter_block:
            if line_stripped.endswith(custom_delimiter):
                stmt = '\n'.join(current_statement)
                stmt = stmt.replace(custom_delimiter, '').strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []
        else:
            if line_stripped.endswith(';'):
                stmt = '\n'.join(current_statement).strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []

    print(f"📋 Found {len(statements)} SQL statements to execute")
    print()

    # Execute each statement
    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        # Get statement type for display
        stmt_lower = statement.lower().strip()
        if stmt_lower.startswith('drop'):
            stmt_type = "DROP TABLE"
        elif stmt_lower.startswith('create table'):
            table_name = statement.split('(')[0].split()[-1]
            stmt_type = f"CREATE TABLE {table_name}"
        elif stmt_lower.startswith('create trigger'):
            trigger_name = statement.split()[2]
            stmt_type = f"CREATE TRIGGER {trigger_name}"
        else:
            stmt_type = "SQL STATEMENT"

        try:
            cursor.execute(statement)
            print(f"✅ [{i}/{len(statements)}] {stmt_type}")
            success_count += 1
        except Exception as e:
            # Some DROP statements may fail if table doesn't exist - that's OK
            if 'drop' in stmt_lower and 'doesn\'t exist' in str(e).lower():
                print(f"⚠️  [{i}/{len(statements)}] {stmt_type} - Table doesn't exist (OK)")
                success_count += 1
            else:
                print(f"❌ [{i}/{len(statements)}] {stmt_type}")
                print(f"   Error: {e}")
                error_count += 1

    connection.commit()
    cursor.close()
    connection.close()

    print()
    print("=" * 70)
    print(f"SETUP COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Errors: {error_count}")
    print()

    if error_count == 0:
        print("🎉 All tables and triggers created successfully!")
        print()
        print("Next steps:")
        print("1. Run: python App.py")
        print("2. Open: http://localhost:5000")
        print("3. Test signup and login!")
        return True
    else:
        print("⚠️  Some errors occurred. Check the errors above.")
        return False

if __name__ == "__main__":
    run_ddl_script()

