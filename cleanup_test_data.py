from utils.database import Database
from utils.cleanup import cleanup_auto_test_data


db = Database()

try:
    result = cleanup_auto_test_data(db)
    print(result)
finally:
    db.close()