class BaseHandler:
    def __init__(self, session):
        self.session = session

    def handle(self):
        raise NotImplementedError("Method not implemented")
