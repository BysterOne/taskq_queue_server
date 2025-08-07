import json
import queue
import threading
from pathlib import Path

import pytest

from task_queue.persistence import PersistenceManager


def _stub_worker(cls: type[PersistenceManager], employer_id: int) -> None:
    cls._queues[employer_id] = queue.Queue()
    cls._locks[employer_id] = threading.Lock()


def test_recover_pending_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PersistenceManager, 'base_path', tmp_path)
    monkeypatch.setattr(PersistenceManager, '_ensure_worker', classmethod(_stub_worker))

    op = {'action': 'add', 'task': {'id': 1, 'duration': 1, 'done_date': None}, 'prev': None}
    PersistenceManager.log(1, op)

    assert not (tmp_path / '1.bac').exists()

    PersistenceManager._queues.clear()
    PersistenceManager._workers.clear()
    PersistenceManager._locks.clear()

    tasks = PersistenceManager.recover(1)

    assert tasks == [{'id': 1, 'duration': 1, 'done_date': None}]
    assert json.loads((tmp_path / '1.bac').read_text()) == tasks
    assert (tmp_path / '1.offset').read_text() == '1'


def test_recover_partial_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PersistenceManager, 'base_path', tmp_path)

    op1 = {'action': 'add', 'task': {'id': 1, 'duration': 1, 'done_date': None}, 'prev': None}
    PersistenceManager.log(1, op1)
    PersistenceManager._queues[1].join()

    PersistenceManager._queues[1].put(None)
    PersistenceManager._workers[1].join()

    PersistenceManager._queues.clear()
    PersistenceManager._workers.clear()
    PersistenceManager._locks.clear()

    op2 = {'action': 'add', 'task': {'id': 2, 'duration': 1, 'done_date': None}, 'prev': 1}
    with (tmp_path / '1.log').open('a', encoding='utf-8') as f:
        f.write(json.dumps(op2) + '\n')

    monkeypatch.setattr(PersistenceManager, '_ensure_worker', classmethod(_stub_worker))

    tasks = PersistenceManager.recover(1)

    assert [t['id'] for t in tasks] == [1, 2]
    assert json.loads((tmp_path / '1.bac').read_text()) == tasks
    assert (tmp_path / '1.offset').read_text() == '2'


def test_recover_clean_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PersistenceManager, 'base_path', tmp_path)

    op = {'action': 'add', 'task': {'id': 1, 'duration': 1, 'done_date': None}, 'prev': None}
    PersistenceManager.log(1, op)
    PersistenceManager._queues[1].join()

    PersistenceManager._queues[1].put(None)
    PersistenceManager._workers[1].join()

    backup = json.loads((tmp_path / '1.bac').read_text())
    offset = (tmp_path / '1.offset').read_text()

    PersistenceManager._queues.clear()
    PersistenceManager._workers.clear()
    PersistenceManager._locks.clear()

    monkeypatch.setattr(PersistenceManager, '_ensure_worker', classmethod(_stub_worker))

    tasks = PersistenceManager.recover(1)

    assert tasks == backup
    assert (tmp_path / '1.offset').read_text() == offset


def test_recover_no_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PersistenceManager, 'base_path', tmp_path)
    monkeypatch.setattr(PersistenceManager, '_ensure_worker', classmethod(_stub_worker))

    tasks = PersistenceManager.recover(1)

    assert tasks == []
    assert not (tmp_path / '1.bac').exists()
    assert not (tmp_path / '1.log').exists()
