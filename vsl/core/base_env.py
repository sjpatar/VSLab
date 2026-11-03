from abc import ABC, abstractmethod

class BaseEnvironment(ABC):
    def __init__(self, app_ref):
        self.app = app_ref
        self.objects = []
        self.toolbar = None

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def render(self, surface):
        pass

    @abstractmethod
    def handle_event(self, event):
        pass