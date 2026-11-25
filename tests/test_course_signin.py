from datetime import datetime, timezone

from src.course_signin import LearnerDeadline, educator_report


def test_report_marks_a_learner_overdue_at_the_deadline():
    due = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
    deadlines = [LearnerDeadline("python-101", "learner-17", due)]

    assert educator_report(deadlines, due) == {"open": 0, "overdue": 1}
