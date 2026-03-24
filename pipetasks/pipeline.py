from abc import ABC, abstractmethod


class Pipeline(ABC):
    name: str | None = None

    @abstractmethod
    def run(self) -> None:
        pass
