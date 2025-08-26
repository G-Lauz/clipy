import dataclasses
import inspect


@dataclasses.dataclass
class Argument:
    name: str
    type: type
    default: any
    help: str

    @property
    def is_required(self):
        return self.default is inspect.Parameter.empty

    @property
    def is_optional(self):
        return self.default is not inspect.Parameter.empty
