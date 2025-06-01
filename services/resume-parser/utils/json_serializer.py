import datetime


def json_serializer(obj):
    """
    Encode Python objects into JSON serializable format.

    This function is used as the default encoder in JSON serialization.
    It handles encoding of datetime.date objects into ISO format.

    Args:
        obj: The Python object to be encoded.

    Returns:
        str: The JSON serializable representation of the object.

    Raises:
        TypeError: If the object is not JSON serializable.
    """
    if isinstance(obj, datetime.date):
        return obj.isoformat()

    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
