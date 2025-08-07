import pytest
from datetime import timedelta, datetime

from task_queue.queue import TaskQueue


@pytest.fixture
def f_queue() -> TaskQueue:
    return TaskQueue()


def test_add_first_task(f_queue, f_task_factory):
    task = f_task_factory(1)
    f_queue.add_task(task)
    assert f_queue._first is task
    assert f_queue._last is task


def test_add_task_without_prev(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    assert f_queue._first is t1
    assert f_queue._last is t2
    assert t1.next is t2
    assert t2.prev is t1


def test_add_task_with_prev(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    f_queue.add_task(t1)
    f_queue.add_task(t2, t1)
    assert f_queue._first is t1
    assert f_queue._last is t2
    assert t1.next is t2
    assert t2.prev is t1


def test_add_task_with_invalid_prev(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    f_queue.add_task(t1)
    with pytest.raises(ValueError):
        f_queue.add_task(t2, t3)


def test_add_existing_task(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    f_queue.add_task(t1)
    with pytest.raises(ValueError):
        f_queue.add_task(t1)


def test_get_task_in_index(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    f_queue.add_task(t1)
    assert f_queue.get_task(1) is t1


def test_get_task_not_in_index_but_in_queue(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    f_queue.add_task(t1)
    f_queue._index.delete(1)
    assert f_queue.get_task(1) is None


def test_get_task_not_in_index_and_not_in_queue(f_queue):
    assert f_queue.get_task(3) is None


def test_del_task_at_start(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.delete_task(t1)
    assert f_queue._first is t2
    assert f_queue._first.prev is None


def test_del_task_in_middle(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    f_queue.delete_task(t2)
    assert f_queue._first.next is t3
    assert f_queue._last.prev is t1


def test_del_task_at_end(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.delete_task(t2)
    assert f_queue._last is t1
    assert f_queue._last.next is None


def test_del_task_not_in_queue(f_queue, f_task_factory):
    t3 = f_task_factory(3)
    with pytest.raises(ValueError):
        f_queue.delete_task(t3)


def test_update_task_in_queue(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    f_queue.add_task(t1)
    t1.duration = timedelta(hours=1).total_seconds()
    t1.done_date = datetime.now().timestamp()
    f_queue.update_task(t1)
    updated_task = f_queue.get_task(1)
    assert updated_task.duration == t1.duration
    assert updated_task.done_date == t1.done_date


def test_update_task_not_in_queue(f_queue, f_task_factory):
    t2 = f_task_factory(2)
    with pytest.raises(ValueError):
        f_queue.update_task(t2)


def test_get_all_tasks(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    assert list(f_queue.get_tasks()) == [t1, t2, t3]


def test_get_tasks_from_task(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    assert list(f_queue.get_tasks(from_task=t2)) == [t2, t3]


def test_get_tasks_to_task(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    assert list(f_queue.get_tasks(to_task=t2)) == [t1, t2]


def test_get_tasks_from_task_to_task(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    assert list(f_queue.get_tasks(from_task=t1, to_task=t2)) == [t1, t2]


def test_move_task_from_start_to_middle(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    t4 = f_task_factory(4)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    f_queue.add_task(t4)
    f_queue.move_task(t1, t2)
    assert list(f_queue.get_tasks()) == [t2, t1, t3, t4]


def test_move_task_from_end_to_start(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    t4 = f_task_factory(4)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    f_queue.add_task(t4)
    f_queue.move_task(t4, None)
    assert list(f_queue.get_tasks()) == [t4, t1, t2, t3]


def test_move_task_from_middle_to_end(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    t4 = f_task_factory(4)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    f_queue.add_task(t4)
    f_queue.move_task(t2, t4)
    assert list(f_queue.get_tasks()) == [t1, t3, t4, t2]


def test_move_task_from_middle_to_middle(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    t4 = f_task_factory(4)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    f_queue.add_task(t4)
    f_queue.move_task(t2, t3)
    assert list(f_queue.get_tasks()) == [t1, t3, t2, t4]


def test_move_task_not_in_queue(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    t3 = f_task_factory(3)
    t4 = f_task_factory(4)
    t5 = f_task_factory(5)
    f_queue.add_task(t1)
    f_queue.add_task(t2)
    f_queue.add_task(t3)
    f_queue.add_task(t4)
    with pytest.raises(ValueError):
        f_queue.move_task(t5, t2)


def test_get_first_task(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    assert f_queue.first_task is None
    f_queue.add_task(t1)
    assert f_queue.first_task is t1
    f_queue.add_task(t2)
    assert f_queue.first_task is t1


def test_get_latest_task(f_queue, f_task_factory):
    t1 = f_task_factory(1)
    t2 = f_task_factory(2)
    assert f_queue.latest_task is None
    f_queue.add_task(t1)
    assert f_queue.latest_task is t1
    f_queue.add_task(t2)
    assert f_queue.latest_task is t2
