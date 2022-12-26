import os
import re
from typing import Any, Dict, List, Optional

# Use the package we installed
from slack_bolt import App, Say
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from bridges.submission_task_bridge import send_cache_feedback
from config.config import BOT_CHANNEL, HOME_ADDRESS, MANDATORY_CHANNEL
from model.model import FileSource, HumanFeedback, Submission, User, engine

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

user_app = App(
    token=os.environ.get("SLACK_BOT_USER_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


def is_official_check(dictionary: Dict[str, Any]):
    for share_key in dictionary:
        public_list: List[str] = dictionary[share_key].keys()
        if os.environ["AUDIO_POSTED_CHANNEL"] in public_list:
            return True

    return False


@app.event("team_join")
def add_new_member_to_db(event: Optional[Dict[str, Any]], say: Say):
    user: Dict[str, Any] = event.get("user")
    with Session(engine) as session:
        find_user_stmt = select(User).where(User.slack_id == user["id"])
        user_obj: User = next(session.scalars(find_user_stmt), None)

        if user_obj:
            user_obj.update_from_dict(user)
        else:
            user_obj = User.from_dict(user)
            session.add(user_obj)
        session.commit()


@app.event("file_shared")
def file_shared_handler(event: Optional[Dict[str, Any]], say: Say):
    with Session(engine) as session:
        file_id = event.get("file_id")
        find_cache_submission = select(Submission).where(
            and_(
                Submission.audio_file == bytes(file_id, encoding="utf-8"),
                Submission.source == FileSource.SLACK,
            )
        )

        cache_submission: Submission = next(
            session.scalars(find_cache_submission), None
        )
        try:
            file_info = app.client.files_info(file=file_id)
        except SlackApiError:
            file_info = {}

        is_official = is_official_check(file_info.get("file", {}).get("shares", {}))

        if cache_submission:
            cache_submission.is_official = is_official
            session.commit()
            send_cache_feedback(app, session, cache_submission)
            return

        find_real_user_id = select(User).where(User.slack_id == event.get("user_id"))
        user: User = next(session.scalars(find_real_user_id), None)

        if not user:
            say("Bot chưa biết bạn là ai. Hãy đợi bot 1 phút để tìm hiểu bạn.")
            return

        new_submission = Submission(
            source=FileSource.SLACK,
            user_id=user.id,
            is_official=is_official,
            audio_file=bytes(event.get("file_id"), encoding="utf-8"),
        )
        session.add(new_submission)
        session.commit()


@app.event({"type": "message"})
def a_likely_feedback_is_posted(event: Optional[Dict[str, Any]], say: Say):

    if (
        "thread_ts" in event and event.get("channel") == MANDATORY_CHANNEL
    ):
        parent_message = app.client.conversations_history(
            channel=MANDATORY_CHANNEL,
            inclusive=True,
            latest=event.get("thread_ts"),
            limit=1,
        ).get("messages")[0]
        file_ids = [x.get("id") for x in parent_message.get("files", [])]

        with Session(engine) as session:
            find_real_user_id = select(User).where(
                User.slack_id == event.get("user")
            )
            user: User = next(session.scalars(find_real_user_id), None)
            if user:
                for file_id in file_ids:
                    find_cache_submission = select(Submission).where(
                        and_(
                            Submission.audio_file == bytes(file_id, encoding="utf-8"),
                            Submission.source == FileSource.SLACK,
                        )
                    )
                    cache_submission: Submission = next(
                        session.scalars(find_cache_submission), None
                    )

                    human_feedback = HumanFeedback(
                        submission_id=cache_submission.id,
                        user_id=user.id,
                        content=event.get("text"),
                    )

                    session.add(human_feedback)

                session.commit()
    
    
    if event.get("channel") not in [MANDATORY_CHANNEL, BOT_CHANNEL]:
        with Session(engine) as session:
            find_real_user_id = select(User).where(
                User.slack_id == event.get("user")
            )
            user: User = next(session.scalars(find_real_user_id), None)

            saved_text = event.get("text")
            if user and user.is_eliminated:
                user_app.client.chat_delete(channel = event.get("channel"), ts=event.get("ts"), as_user=True)
                app.client.chat_postMessage(channel = user.slack_id, text="""Bạn đã bị loại khỏi VietSpeak do không nộp bài hoặc không nhận xét bài đầy đủ cho các thành viên.\nĐể kích hoạt tài khoản trở lại, hãy nộp bài tại kênh <#C01BY57F29H> và nhận xét cho hai bài đăng liền kề.\nLiên hệ admin <@U01C3SM1RRA> để khiếu nại nếu bạn nghĩ việc bạn bị loại là nhầm lẫn.\nBot xin gửi lại tin nhắn bạn vừa nhắn.\n""")
                app.client.chat_postMessage(channel = user.slack_id, text=saved_text)
                return

    
    # function that needs user to be active
    if event.get("text", "").strip().lower() == "login":
        with Session(engine) as session:
            find_real_user_id = select(User).where(
                User.slack_id == event.get("user")
            )
            user: User = next(session.scalars(find_real_user_id), None)
            if user:
                user.password = User.generate_password()
                session.commit()
                app.client.chat_postMessage(channel=user.slack_id, text=f"{HOME_ADDRESS}login?id={user.id}&password={user.password}")


    

    
                



from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


# Start your app
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
