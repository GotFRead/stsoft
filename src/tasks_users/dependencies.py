from typing import Any
from enum import Enum
from datetime import datetime


class SummaryActivityFields(str, Enum):
    HOURS = "hours"
    MINUTES = "minutes"
    CHECK_NEEDED = "check_needed"


class SummaryActivity:
    SummaryActivityCheckNeeded = False

    def __init__(self, hours: int = 0, minutes: int = 0) -> None:
        self.hours = hours
        self.minutes = minutes
        SummaryActivity.SummaryActivityCheckNeeded = True

    def __validate_input(self, name: str, value: Any):

        validate_rules = {
            SummaryActivityFields.HOURS: self.__validate_hours,
            SummaryActivityFields.MINUTES: self.__validate_minutes,
        }[name]

        return validate_rules(value)

    def __setattr__(self, name: str, value: Any) -> None:
        if SummaryActivity.SummaryActivityCheckNeeded is False:
            self.__dict__[name] = value
            return self.__dict__[name]

        if name not in SummaryActivityFields._value2member_map_:
            raise Exception(f"This property '{name}' is UNKNOWN")

        self.__dict__[name] = self.__validate_input(name, value)
        SummaryActivity.SummaryActivityCheckNeeded = True
        return self.__dict__[name]

    def __validate_hours(self, value: Any):
        try:
            result_value = int(value)

            return result_value

        except Exception:
            pass

    def __validate_minutes(self, value: Any):
        try:
            result_value = int(value)

            if result_value >= 60:
                self.hours += result_value // 60
                result_value %= 60

            return result_value

        except Exception:
            pass

    def __str__(self) -> str:
        return f"{self.__format_time_segment(self.hours)}:{self.__format_time_segment(self.minutes)}"

    def __format_time_segment(self, value: int):
        return f"0{value}" if value < 10 else f"{value}"
