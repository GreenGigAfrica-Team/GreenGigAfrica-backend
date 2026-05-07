from apps.tasks.models import Task
from apps.accounts.models import JobSeekerProfile


def get_matched_tasks(profile: JobSeekerProfile, limit: int = 10) -> list:
    """
    Score and rank open tasks for a given profile.
    Algorithm: LGA filter → interest match → urgency boost → volunteer preference.
    """
    qs = Task.objects.filter(
        status=Task.Status.OPEN,
        location_lga=profile.lga,
    ).select_related('organisation')

    # Exclude already accepted tasks
    accepted_ids = profile.user.assignments.values_list('task_id', flat=True)
    qs = qs.exclude(id__in=accepted_ids)

    scored = []
    for task in qs:
        score = 0.0
        if task.task_type in (profile.task_interests or []):
            score += 3.0
        if task.spots_remaining <= 2:
            score += 1.5
        elif task.spots_remaining <= 5:
            score += 0.5
        if profile.user.role == 'volunteer' and task.is_volunteer_only:
            score += 2.0
        scored.append((score, task))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [task for _, task in scored[:limit]]
