
import calendar


def transform_month(value):
    month = calendar.month_abbr[value["month"]]
    year = str(value["year"])[2:]
    value["group"] = month + " " + year
    del value["year"]
    del value["month"]
    return value
