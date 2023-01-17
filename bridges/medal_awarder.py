from typing import List
from utils.task_availability import get_max_task_number, check_if_task_is_available
from sqlalchemy.orm import Session
from model.model import Medal, TaskLevel, Task, User, MedalType
from sqlalchemy import select, and_, delete

def entry_point(session: Session):
    max_task_number = get_max_task_number()
    session.execute(delete(Medal))
    medal_objs: List[Medal] = []
    for task_number in range(1, max_task_number):
        for _, level in TaskLevel._member_map_.items():
            task_id_stmt = select(Task).where(
                and_(Task.task_number == task_number, Task.level == level)
            )
            task: Task = session.scalar(task_id_stmt)
            if not task:
                continue

            number_of_participant_stmt = f"""
                SELECT COUNT(DISTINCT user_id)
                FROM submissions
                WHERE is_official AND task_id={task.id}
            """

            number_of_participants = next(session.execute(number_of_participant_stmt))[
                0
            ]

            if number_of_participants > 3:
                best_members_stmt = f"""
                    SELECT U.id, R.score 
                    FROM (
                        SELECT *
                        FROM (
                            SELECT user_id, score, created_time, dense_rank() OVER (PARTITION BY user_id ORDER BY score DESC, created_time ASC) as ranking 
                            FROM (
                                SELECT user_id, score, created_time
                                FROM submissions
                                WHERE (is_official) AND (task_id={task.id})
                            )
                        )
                        WHERE ranking = 1
                        ORDER BY score DESC, created_time ASC
                        LIMIT 3) R, users U
                    WHERE R.user_id = U.id;
                """

                best_members_result = session.execute(best_members_stmt)
                for rank, result in enumerate(best_members_result):
                    user : User = session.scalar(select(User).where(User.id == result[0]))
                    medal_objs.append(Medal(
                        user_id = user.id,
                        task_id = task.id,
                        medal_type = {
                            0: MedalType.GOLD,
                            1: MedalType.SILVER,
                            2: MedalType.BRONZE
                        }[rank]
                    ))
    
    session.add_all(medal_objs)
    session.commit()