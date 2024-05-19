from datetime import datetime, timedelta
import pytz


def is_today(date: datetime) -> bool:
    result = date + timedelta(days=1) >= datetime.now(
        pytz.timezone("Asia/Taipei")
    ).replace(tzinfo=None)
    return result


def combine_date_time(time_val: float, date_val: datetime):

    year = date_val.year
    month = date_val.month
    day = date_val.day

    time_str = str(round(time_val, 6))

    if len(time_str.split(".")[0]) < 6:
        time_str = "0" + time_str
    time = datetime.strptime(time_str, "%H%M%S.%f")
    return datetime(
        year, month, day, time.hour, time.minute, time.second, time.microsecond
    )


def to_timestamp(time_val: float, date_val: datetime) -> float:
    dt = combine_date_time(time_val, date_val).astimezone(pytz.timezone("Asia/Taipei"))
    ts = dt.timestamp()
    return ts


def today(format: str = None) -> datetime | str:
    if format:
        return datetime.now(pytz.timezone("Asia/Taipei")).strftime(format)
    else:
        return datetime.now(pytz.timezone("Asia/Taipei"))


def kbar_time_formatter(result) -> dict:
    t = str(result.KBar.TimeSn)
    t = "0" + t if len(t) < 4 else t
    d = result.KBar.Date
    kbar = result.KBar.__dict__
    kbar.update({"datetime": datetime.strptime(d + t, "%Y%m%d%H%M")})
    return kbar
