from typing import Optional, List, Any


def normalize_input(data: Any) -> Optional[List[Any]]:
    """
    Normalize input data into an Optional[List[Any]].

    This function handles various input types and normalizes them into a list format.
    It preserves the original data types of the elements when possible.

    Parameters:
    -----------
    data : Any
        The input data to be normalized. Can be of any type.

    Returns:
    --------
    Optional[List[Any]]
        - None if the input is None, an empty string, or an empty iterable.
        - A list of items otherwise, with the following behaviors:
          - Strings are split on commas if they contain any.
          - Lists and tuples have None and empty string values removed.
          - Other types are wrapped in a single-item list.

    Examples:
    ---------
    >>> normalize_input(None)
    None
    >>> normalize_input('')
    None
    >>> normalize_input('a,b,c')
    ['a', 'b', 'c']
    >>> normalize_input(['x', '', None, 'y', 'z'])
    ['x', 'y', 'z']
    >>> normalize_input(42)
    [42]
    >>> normalize_input([1, 'two', 3.0, True])
    [1, 'two', 3.0, True]

    Notes:
    ------
    - Empty strings within lists or tuples are removed.
    - Non-string iterables (e.g., sets, dicts) are wrapped as single items in the returned list.
    """

    if (
        data is None
        or data == ""
        or (isinstance(data, (list, tuple)) and len(data) == 0)
    ):
        return None
    if isinstance(data, str):
        return [item.strip() for item in data.split(",")] if "," in data else [data]
    if isinstance(data, (list, tuple)):
        return [
            item
            for item in data
            if item is not None and (not isinstance(item, str) or item.strip() != "")
        ]
    # For any other type, return as a single-item list
    return [data]
