from typing import List, get_args, get_origin


def is_list(annotations: type) -> bool:
    return get_origin(annotations) == list or annotations == list


def get_list_inner_type(annotations: type) -> type:
    if is_list(annotations):
        inner_types = get_args(annotations)
        return inner_types[0] if inner_types else str
    return str
