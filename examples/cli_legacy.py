"""
An example of a simple CLI with two arguments.
"""

import clipy


@clipy.command()
@clipy.argument("arg1", help="an argument", type=str, required=True)
@clipy.argument("arg2", help="another argument", type=str, required=False)
def main(*_args, arg1, arg2, **_kwargs):
    print("Argument 1:", arg1)
    print("Argument 2:", arg2)


if __name__ == "__main__":
    main()  # pylint: disable=missing-kwoa
