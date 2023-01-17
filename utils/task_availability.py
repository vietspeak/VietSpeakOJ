from model.model import engine, Task
from sqlalchemy.orm import Session
from sqlalchemy import select

def get_max_task_number():
    with Session(engine) as session:
        stmt = """
            SELECT MAX(task_number)
            FROM tasks;
        """

        result = next(session.execute(stmt))
        return result[0]


def check_if_task_is_available(task_number):
    with Session(engine) as session:
        stmt = select(Task).where(Task.task_number == task_number)
        result = next(session.scalars(stmt), None)
        return result is not None