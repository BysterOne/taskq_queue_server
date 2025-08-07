opcodes_map = {}

def register(opcode):
    def wrapper(handler):
        if opcode in opcodes_map:
            raise ValueError(f"Opcode {opcode} already registered")

        opcodes_map[opcode] = handler
        return handler
    return wrapper
