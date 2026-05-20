import json
from datetime import datetime, timedelta


def get_datetime(from_datetime: datetime) -> str:
    "tries is best to make a nice readable datetime msg"
    days = str((from_datetime.date() - datetime.now().date()).days)
    text = """
    {
        "1": "amanhã às %H:%M",
        "0": "hoje às %H:%M",
        "n": "%d/%m/%Y às %H:%M",
        "text": "O token é válido até {0}"
    }
    """
    dic: dict = json.loads(text)
    print(dic)
    fallback = dic.get("n", "%d/%m/%Y às %H:%M")
    print(fallback)
    frm = dic.get(days, fallback)
    print(frm)

    label = from_datetime.strftime(frm)
    print(label)
    text = dic.get("text", "{0}")
    msg = text.format(label)
    # Ses APP_UI_DATETIME_FORMAT
    frm = "%d/%m/%Y %H:%M"
    print(f"APP_DATE_TIME_FORMAT = {frm}, {from_datetime.strftime(frm)}")
    return msg


def main():
    date = datetime.now() + timedelta(hours=120)
    msg = get_datetime(date)
    print(msg)


if __name__ == "__main__":
    main()

# python  testes\\py_test.py
