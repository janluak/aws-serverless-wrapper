from hashlib import blake2b
from json import dumps
from .environ_variables import environ


def delete_keys_in_nested_dict(nested, dict_keys_to_delete):
    """
    Delete keys in a nested dict.
    Tuples and sets are not covered

    Parameters
    ----------
    nested : dict, list
    dict_keys_to_delete : list

    Returns
    -------

    """
    if isinstance(nested, list):
        for i in range(len(nested)):
            nested[i] = delete_keys_in_nested_dict(nested[i], dict_keys_to_delete)
    elif isinstance(nested, dict):
        for key in nested.copy():
            if key in dict_keys_to_delete:
                del nested[key]
            else:
                nested[key] = delete_keys_in_nested_dict(
                    nested[key], dict_keys_to_delete
                )
    return nested


def hash_dict(value):
    """
    Makes a hash from a dictionary with only including other dictionaries & lists
    (and of course strings, numbers etc; just no sets or tuples, that contains
    """
    value = delete_keys_in_nested_dict(value.copy(), environ["dict_hash_ignore_keys"])

    return blake2b(
        str.encode(dumps(value, sort_keys=True)),
        digest_size=environ["dict_hash_digest_size"],
    ).hexdigest()
