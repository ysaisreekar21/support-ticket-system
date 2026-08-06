
import sys
sys.path.append('/Workspace/Users/ysaisreekar@gmail.com/project-ticket-system')
import lakebase

print("=" * 60)
print("SCHEMA CLEANUP SCRIPT")
print("=" * 60)

# List all user schemas
print("\n1. Listing all schemas...")
schemas = lakebase.run_query("""
    SELECT schema_name 
    FROM information_schema.schemata 
    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
    ORDER BY schema_name
""")

print("\nExisting schemas:")
for schema in schemas:
    print(f"  - {schema['schema_name']}")

# Check for old dynamic schema
old_schema = "support_ticket_system_schema_fcf538b2_df6b_49cd_a519_9e9a4719bf86"
schema_exists = any(s['schema_name'] == old_schema for s in schemas)

if schema_exists:
    print(f"\n2. Found old schema: {old_schema}")
    print("   Dropping it (CASCADE will remove all tables)...")
    lakebase.run_write(f"DROP SCHEMA IF EXISTS {old_schema} CASCADE")
    print("   ✓ Old schema dropped successfully")
else:
    print(f"\n2. Old schema '{old_schema}' does not exist (already cleaned up)")

# Verify new schema exists
new_schema = "support_ticket_system"
new_schema_exists = any(s['schema_name'] == new_schema for s in schemas)

if not new_schema_exists:
    print(f"\n3. Creating new schema: {new_schema}")
    lakebase.run_write(f"CREATE SCHEMA IF NOT EXISTS {new_schema}")
    print("   ✓ New schema created")
else:
    print(f"\n3. Schema '{new_schema}' already exists ✓")

# List tables in the new schema
print(f"\n4. Tables in '{new_schema}':")
tables = lakebase.run_query(f"""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = '{new_schema}'
    ORDER BY table_name
""")

if tables:
    for table in tables:
        print(f"  - {new_schema}.{table['table_name']}")
else:
    print("  (No tables yet - they will be created on next app startup)")

# Final verification
print("\n5. Final schema list:")
schemas_final = lakebase.run_query("""
    SELECT schema_name 
    FROM information_schema.schemata 
    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
    ORDER BY schema_name
""")

for schema in schemas_final:
    print(f"  - {schema['schema_name']}")

print("\n" + "=" * 60)
print("CLEANUP COMPLETE")
print("=" * 60)
