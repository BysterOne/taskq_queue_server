import json
import queue
import threading
from pathlib import Path
from typing import Any


class PersistenceManager:
    base_path = Path('storage')
    _queues: dict[int, 'queue.Queue[dict]'] = {}
    _workers: dict[int, threading.Thread] = {}
    _locks: dict[int, threading.Lock] = {}

    @classmethod
    def _log_file(cls, employer_id: int) -> Path:
        cls.base_path.mkdir(exist_ok=True)
        return cls.base_path / f'{employer_id}.log'

    @classmethod
    def _backup_file(cls, employer_id: int) -> Path:
        cls.base_path.mkdir(exist_ok=True)
        return cls.base_path / f'{employer_id}.bac'

    @classmethod
    def _offset_file(cls, employer_id: int) -> Path:
        cls.base_path.mkdir(exist_ok=True)
        return cls.base_path / f'{employer_id}.offset'

    @classmethod
    def _get_offset(cls, employer_id: int) -> int:
        file = cls._offset_file(employer_id)
        return int(file.read_text()) if file.exists() else 0

    @classmethod
    def _set_offset(cls, employer_id: int, value: int) -> None:
        cls._offset_file(employer_id).write_text(str(value))

    @classmethod
    def _load_backup(cls, employer_id: int) -> list[dict[str, Any]]:
        file = cls._backup_file(employer_id)
        if not file.exists():
            return []
        return json.loads(file.read_text())

    @classmethod
    def _write_backup(cls, employer_id: int, tasks: list[dict[str, Any]]) -> None:
        cls._backup_file(employer_id).write_text(json.dumps(tasks))

    @classmethod
    def _apply_op(cls, tasks: list[dict[str, Any]], op: dict[str, Any]) -> None:
        action = op['action']
        if action == 'add':
            task = op['task']
            prev = op.get('prev')
            if prev is None:
                tasks.append(task)
            else:
                idx = next((i for i, t in enumerate(tasks) if t['id'] == prev), len(tasks) - 1)
                tasks.insert(idx + 1, task)
        elif action == 'delete':
            tid = op['task_id']
            tasks[:] = [t for t in tasks if t['id'] != tid]
        elif action == 'update':
            task = op['task']
            for t in tasks:
                if t['id'] == task['id']:
                    t.update(task)
        elif action == 'move':
            tid = op['task_id']
            prev = op.get('prev')
            task = next((t for t in tasks if t['id'] == tid), None)
            if task:
                tasks[:] = [t for t in tasks if t['id'] != tid]
                if prev is None:
                    tasks.insert(0, task)
                else:
                    idx = next((i for i, t in enumerate(tasks) if t['id'] == prev), len(tasks) - 1)
                    tasks.insert(idx + 1, task)

    @classmethod
    def log(cls, employer_id: int, op: dict[str, Any]) -> None:
        log_file = cls._log_file(employer_id)
        with log_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(op) + '\n')
        cls._ensure_worker(employer_id)
        cls._queues[employer_id].put(op)

    @classmethod
    def _ensure_worker(cls, employer_id: int) -> None:
        if employer_id in cls._workers:
            return
        q: 'queue.Queue[dict]' = queue.Queue()
        cls._queues[employer_id] = q
        lock = threading.Lock()
        cls._locks[employer_id] = lock

        def worker() -> None:
            tasks = cls._load_backup(employer_id)
            offset = cls._get_offset(employer_id)
            while True:
                op = q.get()
                if op is None:
                    break
                cls._apply_op(tasks, op)
                with lock:
                    cls._write_backup(employer_id, tasks)
                    offset += 1
                    cls._set_offset(employer_id, offset)
                q.task_done()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        cls._workers[employer_id] = thread

    @classmethod
    def clear(cls, employer_id: int | None = None) -> None:
        if employer_id is None:
            for eid in list(cls._queues.keys()):
                cls.clear(eid)
            return
        q = cls._queues.pop(employer_id, None)
        thread = cls._workers.pop(employer_id, None)
        if q is not None:
            q.put(None)
        if thread is not None:
            thread.join()
        cls._locks.pop(employer_id, None)
        for file in (
            cls._log_file(employer_id),
            cls._backup_file(employer_id),
            cls._offset_file(employer_id),
        ):
            if file.exists():
                file.unlink()

    @classmethod
    def recover(cls, employer_id: int) -> list[dict[str, Any]]:
        tasks = cls._load_backup(employer_id)
        offset = cls._get_offset(employer_id)
        log_file = cls._log_file(employer_id)
        if log_file.exists():
            lines = log_file.read_text().splitlines()
            for line in lines[offset:]:
                if not line:
                    continue
                op = json.loads(line)
                cls._apply_op(tasks, op)
                offset += 1
            cls._write_backup(employer_id, tasks)
            cls._set_offset(employer_id, offset)
        cls._ensure_worker(employer_id)
        return tasks
