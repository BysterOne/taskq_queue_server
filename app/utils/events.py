class Event:
    def __init__(self):
        self.handlers = set()

    def connect(self, handler):
        self.handlers.add(handler)
        return self

    def disconnect(self, handler):
        # noinspection PyBroadException
        try:
            self.handlers.remove(handler)
        except:
            pass
        return self

    def fire(self, *args, **kwargs):
        for handler in self.handlers:
            handler(*args, **kwargs)

    def __iadd__(self, handler):
        return self.connect(handler)

    def __isub__(self, handler):
        return self.disconnect(handler)

    def __call__(self, *args, **kwargs):
        self.fire(*args, **kwargs)
