import dataclasses


@dataclasses.dataclass
class Argument:
    name: str
    type: type
    default: any
    help: str
