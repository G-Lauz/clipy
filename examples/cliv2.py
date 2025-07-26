import clipy


@clipy.Command
def greeting(name: str, times: int = 1):
    """
    Greet someone a specified number of times.

    Args:
        name: The name of the person to greet.
        times:
            The number of times to greet. Defaults to 1.
            one more line for fun
    """
    for _ in range(times):
        print(f"Hello, {name}!")


if __name__ == "__main__":
    greeting()  # pylint: disable=no-value-for-parameter
