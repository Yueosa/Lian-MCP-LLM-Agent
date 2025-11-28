import sys
import os
from pathlib import Path

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from mylib.lian_orm.schema import SchemaManager

def test_schema_parsing():
    sql_path = Path("mylib/lian_orm/schema/LML_SQL.sql").absolute()
    print(f"Loading SQL from: {sql_path}")
    
    manager = SchemaManager(str(sql_path))
    
    print("\n--- Tables Found ---")
    print(manager.all_tables)
    
    print("\n--- Testing Dynamic Methods ---")
    try:
        tasks_table = manager.get_table_tasks()
        print(f"Successfully got table 'tasks': {tasks_table.name}")
        print(f"Primary Key: {tasks_table.primary_key}")
        
        status_field = manager.get_field_tasks('status')
        print(f"Successfully got field 'tasks.status': {status_field.data_type}, Default: {status_field.default}")
        
    except Exception as e:
        print(f"Dynamic method test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Testing Complex Parsing (memory_log) ---")
    try:
        memory_log = manager.get_table_memory_log()
        embedding = memory_log.columns.get('embedding')
        if embedding:
            print(f"Found embedding column: {embedding.data_type}")
        else:
            print("Embedding column not found!")
            
        # Check indices
        print(f"Indices on memory_log: {list(memory_log.indices.keys())}")
        
    except Exception as e:
        print(f"Complex parsing test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_schema_parsing()
