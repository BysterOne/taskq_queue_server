class BaseHandler:
    def __init__(self, session):
        self.session = session

    def handle(self):
        raise NotImplemented("Method not implemented")
