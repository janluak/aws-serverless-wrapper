from decimal import Decimal


__all__ = ["decimal_dict_to_float", "float_dict_to_decimal"]


def decimal_dict_to_float(data):
    """
    Convert all dictionary's decimal values to type=float

    Parameters
    ----------
    data : dict

    Returns
    -------
    dict

    """

    def to_basic(vi):
        if isinstance(vi, Decimal):
            if vi % 1 == 0:
                return int(vi)
            return float(vi)
        return vi

    for k, v in data.items():
        if isinstance(v, dict):
            decimal_dict_to_float(v)
        elif isinstance(v, (list, tuple)):
            data[k] = [
                decimal_dict_to_float(x) if isinstance(x, dict) else to_basic(x)
                for x in v
            ]
        else:
            data[k] = to_basic(v)
    return data


def float_dict_to_decimal(data):
    """
    Convert all dictionary's float values to type=Decimal

    Parameters
    ----------
    data : dict

    Returns
    -------
    dict

    """

    def to_basic(vi):
        if isinstance(vi, float):
            return Decimal(str(vi))
        return vi

    for k, v in data.items():
        if isinstance(v, dict):
            float_dict_to_decimal(v)
        elif isinstance(v, (list, tuple)):
            data[k] = [
                float_dict_to_decimal(x) if isinstance(x, dict) else to_basic(x)
                for x in v
            ]
        else:
            data[k] = to_basic(v)
    return data
