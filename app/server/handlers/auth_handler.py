from .. import opcodes
from ..opcode_utils import register
from .base_handler import BaseHandler


@register(opcodes.CMSG_AUTH_REQUEST)
class AuthHandler(BaseHandler):
    def handle(self):
        password = self.session.read_string()
        self.session.write_opcode(opcodes.SMSG_AUTH_RESPONSE)
        if password == self.session.config.password:
            self.session.write_bool(True)
            self.session.send()
            self.session.is_authenticated = True
        else:
            self.session.write_bool(False)
            self.session.send()
            self.session.close()
