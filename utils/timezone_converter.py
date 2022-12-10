from datetime import datetime

import pytz

FORMAT = "%Y-%m-%d %H:%M:%S"


def timezone_converter(
    timestamp: str, original_timezone_str: str = "UTC", destination_timezone_str: str = 'Asia/Saigon'
) -> str:
    original_timezone = pytz.timezone(original_timezone_str)
    destination_timezone = pytz.timezone(destination_timezone_str)

    return (
        original_timezone.localize(datetime.strptime(timestamp, FORMAT))
        .astimezone(destination_timezone)
        .strftime(FORMAT)
    )
