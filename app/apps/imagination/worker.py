from singleton import Singleton


class ImaginationWorker(metaclass=Singleton):
    def __init__(self) -> None:
        self.task_ids = []

    def add_task(self, task):
        self.task_ids.append(task)


async def update_imagination():
    for task in ImaginationWorker().tasks:
        await task()
