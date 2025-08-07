from concurrent.futures import ThreadPoolExecutor

import pytest


def test_auth_ok(f_auth_client):
    assert f_auth_client.is_authenticated


def test_auth_fail(f_client):
    with pytest.raises(ValueError):
        f_client.authenticate("invalid_password")


def test_get_task_ok(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    f_auth_client.add_task(1, 1, 68.0, 162030.0)
    task = f_auth_client.get_task(1, 1)
    assert task.id == 1


def test_get_task_fail(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    with pytest.raises(ValueError):
        f_auth_client.get_task(1, 999)


def test_add_task_ok(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    f_auth_client.add_task(1, 1, 60.0, 162030.0)


def test_add_task_fail(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    f_auth_client.add_task(1, 1, 60.0, 162030.0)
    with pytest.raises(ValueError):
        f_auth_client.add_task(1, 1, 60.0, 162030.0)


def test_delete_task_ok(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    f_auth_client.add_task(1, 1, 60.0, 162030.0)
    next_task_id = f_auth_client.delete_task(1, 1)
    assert next_task_id == 0


def test_delete_task_fail(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    with pytest.raises(ValueError):
        f_auth_client.delete_task(1, 999)


def test_update_task_ok(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    f_auth_client.add_task(1, 1, 60.0, 162030.0)
    f_auth_client.update_task(1, 1, 120.0, 162040.0)
    task = f_auth_client.get_task(1, 1)
    assert task.id == 1
    assert task.duration == 120.0
    assert task.done_date == 162040.0


def test_update_task_fail(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    with pytest.raises(ValueError):
        f_auth_client.update_task(1, 999, 120.0, 162040.0)


def test_get_task_list_ok(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    tasks = f_auth_client.get_task_list(1)
    assert isinstance(tasks, list)


def test_move_task_ok(f_auth_client, f_queue_factory):
    employer_id = 1
    f_queue_factory(employer_id)
    f_auth_client.add_task(employer_id, 1, 60.0, 162030.0)
    f_auth_client.add_task(employer_id, 2, 120.0, 162040.0)
    f_auth_client.add_task(employer_id, 3, 180.0, 162050.0)

    f_auth_client.move_task(employer_id, 1, 3)
    tasks = f_auth_client.get_task_list(employer_id)
    assert [t.id for t in tasks] == [2, 3, 1]

    f_auth_client.move_task(employer_id, 1, 2)
    tasks = f_auth_client.get_task_list(employer_id)
    assert [t.id for t in tasks] == [2, 1, 3]

    f_auth_client.move_task(employer_id, 1, 0)
    tasks = f_auth_client.get_task_list(employer_id)
    assert [t.id for t in tasks] == [1, 2, 3]

    f_auth_client.delete_task(employer_id, 2)
    f_auth_client.delete_task(employer_id, 3)
    f_auth_client.move_task(employer_id, 1, 0)
    tasks = f_auth_client.get_task_list(employer_id)
    assert [t.id for t in tasks] == [1]


def test_move_task_fail(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    f_auth_client.add_task(1, 1, 60.0, 162030.0)
    with pytest.raises(ValueError):
        f_auth_client.move_task(1, 1, 999)


def test_get_first_task_id_ok(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    first_task_id = f_auth_client.get_first_task_id(1)
    assert isinstance(first_task_id, int)


def test_get_latest_task_id_ok(f_auth_client, f_queue_factory):
    f_queue_factory(1)
    latest_task_id = f_auth_client.get_latest_task_id(1)
    assert isinstance(latest_task_id, int)


def test_create_queue_ok(f_auth_client):
    f_auth_client.create_queue(2)


def test_create_queue_fail(f_auth_client):
    f_auth_client.create_queue(2)
    with pytest.raises(ValueError):
        f_auth_client.create_queue(2)


def test_delete_queue_ok(f_auth_client):
    f_auth_client.create_queue(2)
    f_auth_client.delete_queue(2)


def test_delete_queue_fail(f_auth_client):
    with pytest.raises(ValueError):
        f_auth_client.delete_queue(2)


def test_multithreaded(f_auth_client, f_queue_factory):
    f_queue_factory(1)

    def worker(runner_id: int) -> None:
        for i in range(10):
            f_auth_client.add_task(1, runner_id * 100 + i, 60.0, 162030.0)
            f_auth_client.get_task(1, runner_id * 100 + i)
            f_auth_client.delete_task(1, runner_id * 100 + i)

    futures = [ThreadPoolExecutor(max_workers=10).submit(worker, i) for i in range(10)]
    for future in futures:
        future.result()
