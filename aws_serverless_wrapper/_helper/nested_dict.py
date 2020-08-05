from hashlib import blake2b
from json import dumps
from .environ_variables import environ
from collections.abc import Mapping


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


def update_nested_dict(original_dict, new_values):
    for k, v in new_values.items():
        if isinstance(v, Mapping):
            original_dict[k] = update_nested_dict(original_dict.get(k, {}), v)
        else:
            original_dict[k] = v
    return original_dict


def find_path_values_in_dict(
    data: dict, current_path=None, all_paths=None, all_values=None
):
    if all_values is None:
        all_values = list()
    if all_paths is None:
        all_paths = list()
    if current_path is None:
        current_path = list()
    if isinstance(data, dict):
        for key, value in data.items():
            current_path.append(key)
            if isinstance(value, dict):
                find_path_values_in_dict(value, current_path, all_paths, all_values)
            else:
                all_paths.append(current_path.copy())
                all_values.append(value)
                current_path.pop(-1)
    try:
        current_path.pop(-1)
    except IndexError:
        pass
    return all_paths, all_values
