from typing import List
import os

from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import desc, select, and_, or_
from sqlalchemy.orm import Session
from flask_login import (
    LoginManager,
    login_user,
    current_user,
    login_required,
    logout_user,
)
import markdown
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from slack.app import app as slack_app

from config.config import MAX_NUMBER_OF_SUBMISSIONS_IN_QUEUE
from model.model import Submission, Task, TaskLevel, UserInfo, engine, User
from utils.timezone_converter import timezone_converter
from install.dictionary_loader import ARPABET_TO_IPA
from utils.task_availability import get_max_task_number, check_if_task_is_available

app = Flask(__name__, template_folder="templates")
app.secret_key = bytes(
    os.environ.get("SECRET_KEY", '_5#y2L"F4Q8z\n\xec]/'), encoding="utf-8"
)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memcached://localhost:11211",
    storage_options={},
)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id: str):
    return User.get(user_id)


BUTTON_MAP = {
    TaskLevel.YELLOW: "warning",
    TaskLevel.GREEN: "success",
    TaskLevel.BLUE: "primary",
    TaskLevel.RED: "danger",
}

TASK_STR_MAP = {
    TaskLevel.YELLOW: "Yellow",
    TaskLevel.GREEN: "Green",
    TaskLevel.BLUE: "Blue",
    TaskLevel.RED: "Red",
}


def calculate_progress(session: Session, user_id: int, sound: str) -> float:
    stmt = f"""
        SELECT P.student_sound
        FROM pronunciation_matches P, submissions S
        WHERE S.user_id = {user_id} AND S.is_official AND S.id = P.submission_id AND P.grading_sound='{sound}'
        ORDER BY P.id DESC
        LIMIT 1000;
    """

    results = list(session.execute(stmt))
    if len(results) == 0:
        return None

    numer = 0
    for x in session.execute(stmt):
        student_sound = x[0]
        numer += int(sound == student_sound)

    return numer / len(results)


def make_progress_bar(session: Session, user_id: int, sound: str) -> str:
    number = calculate_progress(session, user_id, sound)
    if number is None:
        return """<p class="font-italic">No data</p>"""

    number = round(number * 100, 2)
    return f"""
    <div class="progress">
        <div class="progress-bar bg-success" role="progressbar" style="width: {number}%" aria-valuenow="{number}" aria-valuemin="0" aria-valuemax="100">{number}%</div>
    </div>
    """


def generate_button(task_number: int, task_level_str: str) -> str:
    task_level_str = task_level_str[0].upper() + task_level_str[1:].lower()
    button_type = BUTTON_MAP[TaskLevel._member_map_[task_level_str.upper()]]

    return f"""
        <a type="button" class="btn btn-{button_type}" href="/tasks?number={task_number}&level={task_level_str}">{task_level_str.upper()} {task_number}</a>
    """


@app.route("/")
def home_page():

    with Session(engine) as session:
        active_user_stmt = """
            SELECT COUNT(*)
            FROM users
            WHERE (NOT is_bot) AND (NOT is_eliminated)
        """

        number_of_active_users = next(session.execute(active_user_stmt))[0]

        submission_stmt = """
            SELECT COUNT(*)
            FROM submissions
        """

        number_of_submissions = next(session.execute(submission_stmt))[0]

        word_error_stmt = """
            SELECT COUNT(*)
            FROM word_errors
        """

        number_of_word_errors = next(session.execute(word_error_stmt))[0]

        pronunciation_error_stmt = """
            SELECT COUNT(*)
            FROM pronunciation_matches
            WHERE (grading_sound != student_sound) OR (student_sound IS NULL)
        """
        number_of_pronunciation_errors = next(
            session.execute(pronunciation_error_stmt)
        )[0]

    return (
        render_template("header.html", page_title="Home")
        + render_template(
            "home_body.html",
            number_of_active_users=number_of_active_users,
            number_of_submissions=number_of_submissions,
            number_of_word_errors=number_of_word_errors,
            number_of_pronunciation_errors=number_of_pronunciation_errors,
        )
        + render_template("footer.html")
    )


@app.route("/tasks", methods=["GET"])
def tasks_page():
    task_number = int(request.values.get("number", get_max_task_number()))

    previous_task_link = (
        f"""
        <a href="/tasks?number={task_number-1}">&#8592; Task {task_number-1}</a>
    """
        if check_if_task_is_available(task_number - 1)
        else ""
    )

    next_task_link = (
        f"""
        <a href="/tasks?number={task_number+1}">Task {task_number+1} &rarr;</a>
    """
        if check_if_task_is_available(task_number + 1)
        else ""
    )

    task_level_str = request.values.get("level", "Yellow")
    task_level = TaskLevel._member_map_.get(task_level_str.upper(), TaskLevel.YELLOW)

    with Session(engine) as session:
        task_stmt = select(Task).where(
            and_(Task.task_number == task_number, Task.level == task_level)
        )
        task_info: Task = session.scalar(task_stmt)

        task_transcript = (
            "".join(f"<p>{x}</p>" for x in task_info.sample_transcript.split("\n"))
            if task_info
            else ""
        )
        task_link = task_info.audio_link if task_info and task_info.audio_link else ""
        task_title = task_info.title if task_info and task_info.title else ""

        for_login_user = []

        if current_user.is_authenticated:
            submission_stmt = (
                select(Submission)
                .where(
                    and_(
                        Submission.user_id == current_user.id,
                        Submission.task_id == task_info.id,
                    )
                )
                .order_by(desc(Submission.id))
                .limit(5)
            )
            result = session.scalars(submission_stmt)
            if result:
                for_login_user.append(
                    """
                    <h2>Your Recent Submissions</h2>
                    <div class="accordion" id="accordionSubmission">
                """
                )
                for sub in result:
                    sub: Submission

                    for_login_user.append(
                        f"""
    <div class="accordion-item">
        <h2 class="accordion-header" id="heading{sub.id}">
        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{sub.id}" aria-expanded="false" aria-controls="collapse{sub.id}">
            {timezone_converter(str(sub.created_time))} ({(sub.score * 100):.2f}/100.00)
        </button>
        </h2>
        <div id="collapse{sub.id}" class="accordion-collapse collapse" aria-labelledby="heading{sub.id}" data-bs-parent="#accordionSubmission">
        <div class="accordion-body">
            {markdown.markdown(sub.generate_feedback_markdown())}<br>

        </div>
        </div>
    </div>

                    """
                    )

                for_login_user.append("</div>")
        for_login_user = "".join(for_login_user)

        return (
            render_template(
                "header.html",
                page_title=f"Task {task_number} {task_level_str} - {task_title}",
            )
            + render_template(
                "tasks_body.html",
                task_number=str(task_number),
                previous_task_link=previous_task_link,
                next_task_link=next_task_link,
                task_level=task_level_str,
                task_link=task_link,
                task_transcript=task_transcript,
                task_title=task_title,
                for_login_user=for_login_user,
            )
            + render_template("footer.html")
        )


@app.route("/status")
def submission_queue():
    result: List[str] = [
        """
        <div class="container"><h1>Status</h1>
        <table class="table">
            <tr>
                <th>#</th>
                <th>Task</th>
                <th>When</th>
            </tr>
    """
    ]
    with Session(engine) as session:
        find_submission_stmt = (
            select(Submission)
            .order_by(desc(Submission.id))
            .limit(MAX_NUMBER_OF_SUBMISSIONS_IN_QUEUE)
        )
        rows: List[Submission] = list(session.scalars(find_submission_stmt))
        for submission in rows:
            if submission.task_id:
                find_task_stmt = select(Task).where(Task.id == submission.task_id)
                task_info: Task = session.scalar(find_task_stmt)
                task_button: str = BUTTON_MAP[task_info.level]
            else:
                task_info: Task = None
                task_button: str = "secondary"

            result.append(
                f"""
            <tr>
                <td>{submission.id}</td>
            """
            )

            button_label = "UNKNOWN"
            if task_info:
                button_label = (
                    f"{str(task_info.level).split('.')[1]} {task_info.task_number}"
                )

            button_link = ""
            if task_info:
                button_link = f"/tasks?number={task_info.task_number}&level={TASK_STR_MAP[task_info.level]}"

            result.append(
                f"""
                    <td><a type="button" class="btn btn-{task_button}" href="{button_link}">{button_label}</a></td>
                """
            )

            result.append(
                f"""
                <td>{timezone_converter(str(submission.created_time))}</td>
            </tr>
            """
            )

    result.append("</table></div>")
    html_source = "\n".join(result)
    return (
        render_template("header.html", page_title="Status")
        + html_source
        + render_template("footer.html")
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    user_id = int(request.values.get("id", 0))
    password = request.values.get("password", "")

    with Session(engine) as session:
        user_stmt = select(User).where(
            and_(
                User.id == user_id,
                and_(User.password == password, User.is_eliminated == False),
            )
        )
        user: User = session.scalar(user_stmt)
        if user:
            login_user(user)

    return redirect(url_for("home_page"))


@app.route("/register", methods=["POST"])
@limiter.limit("10 per day")
def register():
    answers = [
        int((request.values.get(f"question_{i}") or "0").strip()) for i in range(1, 9)
    ]
    if answers == [1, 4, 10, 1, 1, 0, 0, 1]:
        email = request.values.get("email", "")

        if len(email) > 255:
            return f"Địa chỉ email của bạn quá dài. Hãy đăng kí bằng một email khác."

        with Session(engine) as session:
            user_stmt = select(User).where(User.email == email)
            user_obj = session.scalar(user_stmt)

            if user_obj:
                return f"{email} đã được dùng để đăng kí một tài khoản nào đó. Bạn có thể sử dụng chức năng quên mật khẩu của Slack để tìm lại tài khoản này."

            user_info_stmt = select(UserInfo).where(UserInfo.email == email)
            user_info_obj = session.scalar(user_info_stmt)

            if user_info_obj:
                return f"Tài khoản {email} đang chờ để phê duyệt."

            admin_stmt = select(User).where(or_(User.is_admin, User.is_owner))
            admins = session.scalars(admin_stmt)

            for admin in admins:
                admin: User
                slack_app.client.chat_postMessage(
                    text=f"{email} đã điền thành công đơn đăng kí.",
                    channel=admin.slack_id,
                )

            location = request.values.get("question_9", "")[:255]
            user_info = UserInfo(email=email, location=location)

            session.add(user_info)
            session.commit()

        return f"Bạn đã trả lời chính xác các câu hỏi. Trong vòng 12 tiếng tới, một thư mời tham gia nhóm Slack sẽ được gửi đến {email}."

    return "Bạn chưa trả lời chính xác các câu hỏi."


@app.route("/logout")
@login_required
def logout():
    with Session(engine) as session:
        user_stmt: User = select(User).where(User.id == current_user.id)
        user: User = session.scalar(user_stmt)
        user.password = User.generate_password()
        session.commit()
    logout_user()
    return redirect(url_for("home_page"))


@app.route("/syllabus")
def syllabus():
    return (
        render_template("header.html", page_title="Syllabus")
        + render_template("syllabus_body.html")
        + render_template("footer.html")
    )


LIST_OF_SOUNDS = [
    "AH",
    "R",
    "L",
    "S",
    "Z",
    "T",
    "D",
    "TH",
    "DH",
    "F",
    "V",
    "K",
    "G",
    "B",
    "P",
    "AE",
    "AA",
    "IY",
    "IH",
    "UW",
    "UH",
    "SH",
    "ZH",
    "CH",
    "JH",
    "OW",
    "AW",
    "AY",
    "EY",
    "OY",
    "M",
    "N",
    "NG",
    "Y",
    "W",
]


@app.route("/profile")
@login_required
def profile():
    with Session(engine) as session:
        submissions_stmt = f"""
            SELECT DISTINCT task_id
            FROM submissions
            WHERE user_id = {current_user.id} AND is_official
        """
        task_ids = list(session.execute(submissions_stmt))
        number_of_official_submissions = len(task_ids)

        sum_score = 0
        for x in task_ids:
            task_id = x[0]

            find_max_score_stmt = f"""
                SELECT MAX(score)
                FROM submissions
                WHERE user_id = {current_user.id} AND is_official AND task_id = {task_id}
            """
            sum_score += next(session.execute(find_max_score_stmt))[0]

        average_score = sum_score / max(1, number_of_official_submissions)

        primary_stress_progress_bar = make_progress_bar(session, current_user.id, "1")
        secondary_stress_progress_bar = make_progress_bar(session, current_user.id, "2")
        no_stress_progress_bar = make_progress_bar(session, current_user.id, "0")

        pronunciation_table_list = []

        for sound in LIST_OF_SOUNDS:
            pronunciation_table_list.append(
                f"""
                <tr>
                    <th style="width:20%">{ARPABET_TO_IPA[sound]}</th>
                    <td style="width:80%">{make_progress_bar(session, current_user.id, sound)}<td>
                </tr>
            """
            )
        pronunciation_table = "".join(pronunciation_table_list)

        gold_medal_stmt = f"""
            SELECT COUNT(*) FROM medals WHERE user_id={current_user.id} AND medal_type='GOLD'        
        """

        gold_medals = next(session.execute(gold_medal_stmt))[0]

        silver_medal_stmt = f"""
            SELECT COUNT(*) FROM medals WHERE user_id={current_user.id} AND medal_type='SILVER'        
        """

        silver_medals = next(session.execute(silver_medal_stmt))[0]

        bronze_medal_stmt = f"""
            SELECT COUNT(*) FROM medals WHERE user_id={current_user.id} AND medal_type='BRONZE'        
        """

        bronze_medals = next(session.execute(bronze_medal_stmt))[0]

        rating_ranking_stmt = f"""
            SELECT rating_ranking 
            FROM
                (
                    WITH rating_temp AS (
                        SELECT user_id, value, dense_rank() OVER (PARTITION BY user_id ORDER BY id DESC) as time_ranking
                        FROM rating
                    )
                    SELECT user_id, value, dense_rank() OVER (ORDER BY value DESC) as rating_ranking FROM rating_temp WHERE time_ranking=1
                )
            WHERE user_id={current_user.id};
        """

        rating_ranking_obj = next(session.execute(rating_ranking_stmt), None)
        rating_ranking_str = ""
        if rating_ranking_obj:
            rating_ranking_str = f"(#{rating_ranking_obj[0]})"

        rating_history_data = current_user.get_rating_history()
        min_task_to_max_task_list = []
        max_rating_score = 1500
        if rating_history_data:
            min_task_to_max_task_list = list(
                range(rating_history_data[0]["x"], rating_history_data[-1]["x"] + 1)
            )
            max_rating_score = max(i["y"] for i in rating_history_data)

        return (
            render_template("header.html", page_title="Profile")
            + render_template(
                "profile_body.html",
                username=current_user.display_name,
                number_of_official_submissions=number_of_official_submissions,
                average_score=f"{(average_score*100):.2f}",
                primary_stress_progress_bar=primary_stress_progress_bar,
                secondary_stress_progress_bar=secondary_stress_progress_bar,
                no_stress_progress_bar=no_stress_progress_bar,
                pronunciation_table=pronunciation_table,
                gold_medals=gold_medals,
                silver_medals=silver_medals,
                bronze_medals=bronze_medals,
                rating_score=round(current_user.get_rating()),
                max_rating_score=max_rating_score,
                rating_ranking_str=rating_ranking_str,
                min_task_to_max_task_list=min_task_to_max_task_list,
                rating_history_data=rating_history_data,
            )
            + render_template("footer.html")
        )


@app.route("/ranking", methods=["GET"])
def ranking_page():

    max_task_number = get_max_task_number()
    task_number = int(request.values.get("number", max_task_number))

    previous_task_link = (
        f"""
        <a href="/ranking?number={task_number-1}">&#8592; Task {task_number-1}</a>
    """
        if check_if_task_is_available(task_number - 1)
        else ""
    )

    next_task_link = (
        f"""
        <a href="/ranking?number={task_number+1}">Task {task_number+1} &rarr;</a>
    """
        if check_if_task_is_available(task_number + 1)
        else ""
    )

    table_inner_code = []

    with Session(engine) as session:
        for level_str, level in TaskLevel._member_map_.items():
            print(level_str, level)
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
                table_inner_code.append(
                    f"""
                    <tr>
                        <th colspan=3>{generate_button(task_number, level_str)}</th>
                    </tr>
                    <tr>
                        <td colspan=3>Số bạn tham gia task này: {number_of_participants}</td>
                    </tr>
                    <tr>
                        <th>#</th>
                        <th>Thành viên</th>
                        <th>Điểm</th>
                    </tr>
                """
                )

                best_members_stmt = f"""
                    SELECT U.display_name, R.score 
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
                    table_inner_code.append(
                        f"""
                        <tr>
                            <td>{rank+1}</td>
                            <td>{result[0] if current_user.is_authenticated and task_number < max_task_number else '???'}</td>
                            <td>{(result[1] * 100):.2f}</td>
                        </tr>
                    """
                    )

    return (
        render_template(
            "header.html",
            page_title=f"Ranking - Task {task_number}",
        )
        + render_template(
            "ranking_body.html",
            task_number=str(task_number),
            previous_task_link=previous_task_link,
            next_task_link=next_task_link,
            table_inner_code="".join(table_inner_code),
        )
        + render_template("footer.html")
    )
