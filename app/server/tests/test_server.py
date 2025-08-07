from server import opcodes


def test_auth_ok(f_auth_client):
    assert f_auth_client is not None


def test_auth_fail(f_client):
    f_client.write_opcode(opcodes.CMSG_AUTH_REQUEST)
    f_client.write_string("wrong_password")
    f_client.send()

    opcode = f_client.read_opcode()
    assert opcode == opcodes.SMSG_AUTH_RESPONSE
    result = f_client.read_bool()
    assert not result
