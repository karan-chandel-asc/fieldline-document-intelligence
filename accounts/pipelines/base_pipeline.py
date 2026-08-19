from abc import ABC, abstractmethod


class BasePipeline(ABC):
    """Every pipeline orchestrates one or more services to fulfil a single
    use case and must return a (success, message, payload) tuple."""

    @abstractmethod
    def process_item(self, data):
        raise NotImplementedError
