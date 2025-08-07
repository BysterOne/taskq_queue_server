from task_queue.manager import QueueManager

from .. import opcodes
from ..opcode_utils import register
from .base_handler import BaseHandler


@register(opcodes.CMSG_QUEUE_CREATE_REQUEST)
class QueueCreateRequestHandler(BaseHandler):
    def handle(self):
        employer_id = self.session.read_int()
        self.session.write_opcode(opcodes.SMSG_QUEUE_CREATE_RESPONSE)
        try:
            QueueManager.create_queue(employer_id)
            self.session.write_bool(True)
            self.session.send()
        except ValueError as e:
            self.session.write_bool(False)
            self.session.write_string(str(e))
            self.session.send()
            self.session.close()


@register(opcodes.CMSG_QUEUE_DELETE_REQUEST)
class QueueDeleteRequestHandler(BaseHandler):
    def handle(self):
        employer_id = self.session.read_int()
        self.session.write_opcode(opcodes.SMSG_QUEUE_DELETE_RESPONSE)
        try:
            QueueManager.delete_queue(employer_id)
            self.session.write_bool(True)
            self.session.send()
        except ValueError as e:
            self.session.write_bool(False)
            self.session.write_string(str(e))
            self.session.send()
            self.session.close()
