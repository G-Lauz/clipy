"""
Example of reading argument values from a configuration file.
"""

import dataclasses

import clipy


@dataclasses.dataclass
class OptimizerConfig(clipy.Config):
    """
    Optimizer settings.

    Args:
        lr: Learning rate
        momentum: SGD momentum
    """

    lr: float = 0.001
    momentum: float = 0.9


@dataclasses.dataclass
class TrainConfig(clipy.Config):
    """
    Training settings.

    Args:
        name: Name of the run
        epochs: Number of training epochs
        tags: Labels to attach to the run
        optimizer: Optimizer settings
    """

    name: str  # no default, so the file must provide it
    epochs: int = 10
    tags: list = dataclasses.field(default_factory=list)

    # A nested config needs `default_factory`: a dataclass refuses a mutable
    # default, so `= OptimizerConfig()` would raise at class creation.
    optimizer: OptimizerConfig = dataclasses.field(default_factory=OptimizerConfig)


@clipy.Command
def train(config: TrainConfig):
    """
    Train a model using settings read from a configuration file.

    Args:
        config: Path to the training configuration file
    """
    print(f"Training '{config.name}' for {config.epochs} epochs")
    print(f"  learning rate: {config.optimizer.lr}")
    print(f"  momentum:      {config.optimizer.momentum}")


if __name__ == "__main__":
    train()  # pylint: disable=no-value-for-parameter
