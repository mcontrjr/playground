#!/bin/python3

from datetime import datetime, timedelta

delta = timedelta(weeks=2)
payday=datetime(year=2026, month=1, day=9)
current_month=payday.month
end_date=datetime(year=2026, month=12, day=31)
golden_month=[]
counter = 0
months = {
    1: "jan",
    2: "feb",
    3:"march",
    4:"april",
    5:"may",
    6:"june",
    7:"july",
    8:"aug",
    9:"sept",
    10:"oct",
    11:"nov",
    12:"dec"
}

while payday <= end_date:
    if current_month == payday.month:
        counter+=1
    else:
        if counter > 2:
            golden_month.append(current_month)
        current_month = payday.month
        counter = 1
    payday+=delta
    if payday.year > end_date.year:
        break

print(f"Golden months for 2026:")
for month in golden_month:
    print(months[month])
