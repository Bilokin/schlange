von abc importiere ABC, abstractmethod


klasse Collector(ABC):
    @abstractmethod
    def collect(self, stack_frames):
        """Collect profiling data von stack frames."""

    @abstractmethod
    def export(self, filename):
        """Export collected data to a file."""
