from typing import Any, Dict, List
from utils.task_availability import get_max_task_number, check_if_task_is_available
from sqlalchemy.orm import Session
from model.model import Rating, TaskLevel, Task, User, MedalType
from sqlalchemy import select, and_, delete


def entry_point(session: Session):
    max_task_number = get_max_task_number()

    session.execute(delete(Rating))
    session.commit()

    for task_number in range(1, max_task_number + 1):
        for _, level in TaskLevel._member_map_.items():
            task_id_stmt = select(Task).where(
                and_(Task.task_number == task_number, Task.level == level)
            )
            task: Task = session.scalar(task_id_stmt)
            if not task:
                continue

            participant_stmt = f"""
                SELECT user_id, MAX(score)
                FROM submissions
                WHERE is_official AND task_id={task.id}
                GROUP BY user_id
            """

            user_data: List[Dict[str, Any]] = []
            for result in session.execute(participant_stmt):
                user_obj: User = session.scalar(
                    select(User).where(User.id == result[0])
                )
                user_data.append(
                    {
                        "user_id": user_obj.id,
                        "score": result[1],
                        "rating": user_obj.get_rating(),
                    }
                )

            n = len(user_data)

            if n < 2:
                continue

            user_data.sort(key=lambda x: x["score"], reverse=True)
            rnd = n - 1 + n % 2
            schedule = [[] for i in range(rnd)]
            for i in range(rnd):
                for j in range(i, rnd):
                    if i == j:
                        if n % 2 == 0:
                            schedule[(i + j) % rnd].append(
                                [user_data[i], user_data[n - 1]]
                            )
                    else:
                        schedule[(i + j) % rnd].append([user_data[i], user_data[j]])

            for i in range(rnd):
                for match in schedule[i]:
                    a = match[0]
                    b = match[1]
                    ea = 1 / (1 + 10 ** ((b["rating"] - a["rating"]) / 400))
                    eb = 1 / (1 + 10 ** ((a["rating"] - b["rating"]) / 400))
                    sa = 0
                    if a["score"] > b["score"] or a["score"] == 1:
                        sa = 1
                    if a["score"] == b["score"]:
                        sa = 0.5
                    sb = 1 - sa

                    if b["score"] == 1:
                        sb = 1

                    ka = 0
                    if a["rating"] < 2300:
                        ka = 400
                    if 2300 <= a["rating"] < 2400:
                        ka = 200
                    if a["rating"] >= 2400:
                        ka = 100
                    kb = 0
                    if b["rating"] < 2300:
                        kb = 400
                    if 2300 <= b["rating"] < 2400:
                        kb = 200
                    if b["rating"] >= 2400:
                        kb = 100
                    ka /= n - 1
                    kb /= n - 1

                    a["rating"] = a["rating"] + ka * (sa - ea)
                    b["rating"] = b["rating"] + kb * (sb - eb)

            rating_objs: List[Rating] = []
            for u in user_data:
                rating_objs.append(
                    Rating(user_id=u["user_id"], task_id=task.id, value=u["rating"])
                )
            session.add_all(rating_objs)
            session.commit()
