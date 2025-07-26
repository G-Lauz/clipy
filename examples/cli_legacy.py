"""
An example of a simple CLI with two arguments.
"""

import clipy_legacy


@clipy_legacy.command()
@clipy_legacy.argument("arg1", help="an argument", type=str, required=True)
@clipy_legacy.argument("arg2", help="another argument", type=str, required=False)
def main(*_args, arg1, arg2, **_kwargs):
    print("Argument 1:", arg1)
    print("Argument 2:", arg2)


if __name__ == "__main__":
    main()  # pylint: disable=missing-kwoa
