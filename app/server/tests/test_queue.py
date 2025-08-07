from server import opcodes


def test_get_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q2 = f_queue_factory(2)
    q1.add_task(f_task_factory(1, 10))
    q2.add_task(f_task_factory(2, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_GET)
    f_auth_client.write_int(1)
    f_auth_client.write_int(1)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK
    assert f_auth_client.read_bool()
    assert f_auth_client.read_int() == 0
    assert f_auth_client.read_int() == 0
    assert f_auth_client.read_float() == 10
    assert f_auth_client.read_float() == 0


def test_get_task_not_found(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_GET)
    f_auth_client.write_int(1)
    f_auth_client.write_int(3)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "Task not found."


def test_get_task_invalid_queue(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_GET)
    f_auth_client.write_int(1)
    f_auth_client.write_int(2)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "Task not found."


def test_add_task(f_auth_client, f_queue_factory, f_task_factory):
    f_queue_factory(1)

    f_auth_client.write_opcode(opcodes.CMSG_TASK_ADD)
    f_auth_client.write_int(1)
    f_auth_client.write_int(3)
    f_auth_client.write_float(10)
    f_auth_client.write_float(0)
    f_auth_client.write_int(0)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_ADD
    assert f_auth_client.read_bool()


def test_add_task_invalid_queue(f_auth_client):
    f_auth_client.write_opcode(opcodes.CMSG_TASK_ADD)
    f_auth_client.write_int(2)
    f_auth_client.write_int(3)
    f_auth_client.write_float(10)
    f_auth_client.write_float(0)
    f_auth_client.write_int(0)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_ADD
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "No queue for employer_id 2"


def test_add_task_prev_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_ADD)
    f_auth_client.write_int(1)
    f_auth_client.write_int(3)
    f_auth_client.write_float(10)
    f_auth_client.write_float(0)
    f_auth_client.write_int(1)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_ADD
    assert f_auth_client.read_bool()
    tasks = list(q1.get_tasks())
    assert [t.id for t in tasks] == [1, 3, 2]


def test_add_task_invalid_prev_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_ADD)
    f_auth_client.write_int(1)
    f_auth_client.write_int(3)
    f_auth_client.write_float(10)
    f_auth_client.write_float(0)
    f_auth_client.write_int(3)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_ADD
    assert not f_auth_client.read_bool()
    assert (
        f_auth_client.read_string()
        == "'prev_task_id' is invalid. May be the task not in the queue."
    )


def test_delete_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_DELETE)
    f_auth_client.write_int(1)
    f_auth_client.write_int(2)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_DELETE
    assert f_auth_client.read_bool()
    assert [t.id for t in q1.get_tasks()] == [1]


def test_delete_task_not_found(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_DELETE)
    f_auth_client.write_int(1)
    f_auth_client.write_int(3)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_DELETE
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "Task not found."


def test_delete_task_invalid_queue(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_DELETE)
    f_auth_client.write_int(2)
    f_auth_client.write_int(2)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_DELETE
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "No queue for employer_id 2"


def test_update_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_UPDATE)
    f_auth_client.write_int(1)
    f_auth_client.write_int(2)
    f_auth_client.write_float(20)
    f_auth_client.write_float(0)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_UPDATE
    assert f_auth_client.read_bool()
    assert q1.get_task(2).duration == 20


def test_update_task_not_found(f_auth_client, f_queue_factory, f_task_factory):
    f_queue_factory(1)

    f_auth_client.write_opcode(opcodes.CMSG_TASK_UPDATE)
    f_auth_client.write_int(1)
    f_auth_client.write_int(3)
    f_auth_client.write_float(20)
    f_auth_client.write_float(0)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_UPDATE
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "Task not found."


def test_update_task_invalid_queue(f_auth_client, f_queue_factory, f_task_factory):
    f_queue_factory(1)

    f_auth_client.write_opcode(opcodes.CMSG_TASK_UPDATE)
    f_auth_client.write_int(2)
    f_auth_client.write_int(2)
    f_auth_client.write_float(20)
    f_auth_client.write_float(0)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_UPDATE
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "No queue for employer_id 2"


def test_list_tasks(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_LIST)
    f_auth_client.write_int(1)
    f_auth_client.write_int(1)
    f_auth_client.write_int(3)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_LIST
    assert f_auth_client.read_bool()
    tasks = []
    while True:
        task_id = f_auth_client.read_int()
        if task_id == 0:
            break
        duration = f_auth_client.read_float()
        done_date = f_auth_client.read_float()
        tasks.append((task_id, duration, done_date))
    assert tasks == [(1, 10, 0), (2, 10, 0), (3, 10, 0)]


def test_list_all_tasks(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_LIST)
    f_auth_client.write_int(1)
    f_auth_client.write_int(0)
    f_auth_client.write_int(0)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_LIST
    assert f_auth_client.read_bool()
    tasks = []
    while True:
        task_id = f_auth_client.read_int()
        if task_id == 0:
            break
        duration = f_auth_client.read_float()
        done_date = f_auth_client.read_float()
        tasks.append((task_id, duration, done_date))
    assert tasks == [(1, 10, 0), (2, 10, 0), (3, 10, 0)]


def test_list_tasks_not_found(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_LIST)
    f_auth_client.write_int(1)
    f_auth_client.write_int(4)
    f_auth_client.write_int(5)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_LIST
    assert not f_auth_client.read_bool()
    assert (
        f_auth_client.read_string()
        == "'from_task_id' is invalid. May be the task not in the queue."
    )


def test_list_tasks_invalid_queue(f_auth_client):
    f_auth_client.write_opcode(opcodes.CMSG_TASK_LIST)
    f_auth_client.write_int(2)
    f_auth_client.write_int(1)
    f_auth_client.write_int(3)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_LIST
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "No queue for employer_id 2"


def test_list_tasks_invalid_from_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_LIST)
    f_auth_client.write_int(1)
    f_auth_client.write_int(4)
    f_auth_client.write_int(3)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_LIST
    assert not f_auth_client.read_bool()
    assert (
        f_auth_client.read_string()
        == "'from_task_id' is invalid. May be the task not in the queue."
    )


def test_move_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))
    q1.add_task(f_task_factory(4, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_MOVE)
    f_auth_client.write_int(1)
    f_auth_client.write_int(2)
    f_auth_client.write_int(4)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_MOVE
    assert f_auth_client.read_bool()
    assert [t.id for t in q1.get_tasks()] == [1, 3, 4, 2]


def test_move_task_not_found(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))
    q1.add_task(f_task_factory(4, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_MOVE)
    f_auth_client.write_int(1)
    f_auth_client.write_int(5)
    f_auth_client.write_int(4)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_MOVE
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "Task not found."


def test_move_task_invalid_queue(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))
    q1.add_task(f_task_factory(4, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_MOVE)
    f_auth_client.write_int(2)
    f_auth_client.write_int(2)
    f_auth_client.write_int(4)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_MOVE
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "No queue for employer_id 2"


def test_move_task_invalid_prev_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_MOVE)
    f_auth_client.write_int(1)
    f_auth_client.write_int(2)
    f_auth_client.write_int(5)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_MOVE
    assert not f_auth_client.read_bool()
    assert (
        f_auth_client.read_string()
        == "'prev_task_id' is invalid. May be the task not in the queue."
    )


def test_move_task_invalid_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))
    q1.add_task(f_task_factory(4, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_MOVE)
    f_auth_client.write_int(1)
    f_auth_client.write_int(5)
    f_auth_client.write_int(4)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_MOVE
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "Task not found."


def test_first_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_FIRST)
    f_auth_client.write_int(1)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_FIRST
    assert f_auth_client.read_bool()
    assert f_auth_client.read_int() == 1


def test_first_task_not_found(f_auth_client):
    f_auth_client.write_opcode(opcodes.CMSG_TASK_FIRST)
    f_auth_client.write_int(2)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_FIRST
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "No queue for employer_id 2"


def test_latest_task(f_auth_client, f_queue_factory, f_task_factory):
    q1 = f_queue_factory(1)
    q1.add_task(f_task_factory(1, 10))
    q1.add_task(f_task_factory(2, 10))
    q1.add_task(f_task_factory(3, 10))

    f_auth_client.write_opcode(opcodes.CMSG_TASK_LATEST)
    f_auth_client.write_int(1)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_LATEST
    assert f_auth_client.read_bool()
    assert f_auth_client.read_int() == 3


def test_latest_task_not_found(f_auth_client):
    f_auth_client.write_opcode(opcodes.CMSG_TASK_LATEST)
    f_auth_client.write_int(2)
    f_auth_client.send()

    assert f_auth_client.read_opcode() == opcodes.SMSG_TASK_LATEST
    assert not f_auth_client.read_bool()
    assert f_auth_client.read_string() == "No queue for employer_id 2"
