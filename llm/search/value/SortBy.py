from enum import Enum

class SortBy(str, Enum):
    STARS = "stars"
    FORKS = "forks"
    HELP_WANTED_ISSUES = "help-wanted-issues"
    UPDATED = "updated"
    BEST_MATCH= "best-match"

