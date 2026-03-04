from backend.app.db import get_phones_collection

coll = get_phones_collection()

# Delete all documents
result = coll.delete_many({})
print("Deleted", result.deleted_count, "documents")