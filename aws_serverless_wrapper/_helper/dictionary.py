def delete_keys_in_nested_dict(nested_dict, dict_keys_to_delete):
    """
    Delete keys in a nested dict.
    Tuples and sets are not covered

    Parameters
    ----------
    nested_dict : dict, list
    dict_keys_to_delete : list

    Returns
    -------

    """
    if isinstance(nested_dict, list):
        for i in range(len(nested_dict)):
            nested_dict[i] = delete_keys_in_nested_dict(nested_dict[i], dict_keys_to_delete)
    elif isinstance(nested_dict, dict):
        for key in nested_dict.copy():
            if key in dict_keys_to_delete:
                del nested_dict[key]
            else:
                nested_dict[key] = delete_keys_in_nested_dict(nested_dict[key], dict_keys_to_delete)
    return nested_dict
