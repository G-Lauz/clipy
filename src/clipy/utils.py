from typing import Tuple, get_args, get_origin


def is_list(annotations: type) -> bool:
    return get_origin(annotations) == list or annotations == list


def get_list_inner_type(annotations: type) -> type:
    if is_list(annotations):
        inner_types = get_args(annotations)
        return inner_types[0] if inner_types else str
    return str


def is_dict(annotations: type) -> bool:
    return get_origin(annotations) == dict or annotations == dict


def get_dict_key_value_types(annotations: type) -> Tuple[type, type]:
    if is_dict(annotations):
        inner_types = get_args(annotations)
        key_type = inner_types[0] if inner_types else str
        value_type = inner_types[1] if len(inner_types) > 1 else str
        return key_type, value_type
    return str, str
