import uuid

def check_is_valid_uuid(s: str) -> bool:
    try:
        uuid_obj = uuid.UUID(s)
        return str(uuid_obj) == s.lower()
    except ValueError:
        print(f"ValueError: {s} is not a valid UUID.")
        return False