import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta

# Add src to sys.path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

from fecha_contador.models import ImportantDate, parse_datetime
from fecha_contador.service import DateCounterService
from fecha_contador.storage import JsonStorage

def test_migration():
    # Test loading old format (missing group, date as string YYYY-MM-DD)
    temp_file = Path("test_migration.json")
    try:
        with open(temp_file, "w") as f:
            f.write('[{"name": "Old Date", "date": "2026-01-01", "created_at": "2025-12-01"}]')
        
        storage = JsonStorage(temp_file)
        service = DateCounterService(storage)
        dates = service.list_dates()
        
        assert len(dates) == 1
        assert dates[0].name == "Old Date"
        assert dates[0].group == "General" # Default
        assert dates[0].date == datetime(2026, 1, 1)
        print("Migration test passed!")
    finally:
        if temp_file.exists(): temp_file.unlink()

def test_groups():
    temp_file = Path("test_groups.json")
    try:
        storage = JsonStorage(temp_file)
        service = DateCounterService(storage)
        
        d1 = ImportantDate("Task 1", datetime(2026, 1, 1), group="Work")
        d2 = ImportantDate("Task 2", datetime(2026, 1, 2), group="Personal")
        
        service.add_date(d1)
        service.add_date(d2)
        
        groups = service.get_groups()
        assert "Work" in groups
        assert "Personal" in groups
        assert len(groups) == 2
        
        service.move_to_group("Task 1", "Personal")
        dates = service.list_dates()
        assert all(d.group == "Personal" for d in dates)
        print("Groups test passed!")
    finally:
        if temp_file.exists(): temp_file.unlink()

if __name__ == "__main__":
    print("Running verification tests...")
    try:
        test_migration()
        test_groups()
        print("All tests passed successfully!")
    except Exception as e:
        print(f"Tests failed: {e}")
        sys.exit(1)
