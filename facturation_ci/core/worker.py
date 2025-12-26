import asyncio
from PyQt6.QtCore import QObject, pyqtSignal

class Worker(QObject):
    """
    Generic worker to run a function in a separate thread.
    Especially useful for running asyncio tasks from a sync Qt context.
    """
    finished = pyqtSignal(object)  # Emits the return value of the function
    error = pyqtSignal(str)        # Emits the error message if an exception occurs
    progress = pyqtSignal(str)     # Emits progress updates

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """
        Executes the target function.
        If the function is a coroutine, it runs it in an asyncio event loop.
        """
        try:
            if asyncio.iscoroutinefunction(self.fn):
                # If the function is async, run it in a new event loop
                result = asyncio.run(self.fn(*self.args, **self.kwargs))
            else:
                # If it's a regular function, just call it
                result = self.fn(*self.args, **self.kwargs)

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"An error occurred: {e}")
