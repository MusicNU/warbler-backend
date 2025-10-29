import uuid

def valid_uuid(s: str) -> bool:
    try:
        uuid_obj = uuid.UUID(s)
        return str(uuid_obj) == s.lower()
    except ValueError:
        print(f"ValueError: {s} is not a valid UUID.")
        return False
    
def s3_object_exists(s3, bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        print(f"Error encountered in trying to find key={key} in AWS bucket={bucket}")
        print(str(e))
        return False