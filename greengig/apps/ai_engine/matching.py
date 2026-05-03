"""
AI job matching — recommends tasks to job seekers based on their profile.

Algorithm (MVP):
  1. Filter tasks by user's LGA (hard constraint)
  2. Score remaining tasks by interest overlap (task_type in user's task_interests)
  3. Boost tasks with fewer spots remaining (urgency signal)
  4. Return top-N ranked tasks

Post-MVP: replace with a proper collaborative filtering or embedding-based model.
"""
from apps.tasks.models import Task
from apps.accounts.models import JobSeekerProfile


def get_matched_tasks(profile: JobSeekerProfile, limit: int = 10) -> list:
    """
    Return a ranked list of Task objects for the given profile.
    """
    # Step 1: base queryset — open tasks in user's LGA
    qs = Task.objects.filter(
        status=Task.Status.OPEN,
        location_lga=profile.lga,
    ).select_related("organisation")

    # Exclude tasks the user has already accepted
    accepted_task_ids = profile.user.assignments.values_list("task_id", flat=True)
    qs = qs.exclude(id__in=accepted_task_ids)

    tasks = list(qs)

    # Step 2: score each task
    scored = []
    for task in tasks:
        score = 0.0

        # Interest match — +3 per matching interest
        if task.task_type in (profile.task_interests or []):
            score += 3.0

        # Urgency — tasks with fewer spots get a small boost
        if task.spots_remaining <= 2:
            score += 1.5
        elif task.spots_remaining <= 5:
            score += 0.5

        # Volunteer preference — if user is a volunteer, boost volunteer tasks
        if profile.user.role == "volunteer" and task.is_volunteer_only:
            score += 2.0

        scored.append((score, task))

    # Step 3: sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)

    return [task for _, task in scored[:limit]]
