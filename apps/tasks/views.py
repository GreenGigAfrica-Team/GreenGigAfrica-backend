from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organisations.models import Organisation
from .models import Task, TaskAssignment
from .serializers import TaskSerializer, TaskCreateSerializer, TaskAssignmentSerializer, MyTaskSerializer


def _get_approved_org(user):
    try:
        org = user.organisation
        if org.is_approved:
            return org
    except Organisation.DoesNotExist:
        pass
    return None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def task_list_create(request):
    if request.method == 'GET':
        qs = Task.objects.filter(status=Task.Status.OPEN).select_related('organisation')

        lga = request.query_params.get('lga')
        task_type = request.query_params.get('task_type')
        volunteer_only = request.query_params.get('volunteer_only')

        if lga:
            qs = qs.filter(location_lga=lga)
        if task_type:
            qs = qs.filter(task_type=task_type)
        if volunteer_only is not None:
            qs = qs.filter(is_volunteer_only=volunteer_only.lower() == 'true')

        # Default: filter by user's LGA if profile exists
        if not lga and hasattr(request.user, 'profile'):
            qs = qs.filter(location_lga=request.user.profile.lga)

        return Response(TaskSerializer(qs, many=True).data)

    # POST — only approved orgs
    org = _get_approved_org(request.user)
    if not org:
        return Response(
            {'detail': 'Only approved organisations can post tasks.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = TaskCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    task = serializer.save(organisation=org)
    return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def task_detail(request, task_id):
    try:
        task = Task.objects.select_related('organisation').get(pk=task_id)
    except Task.DoesNotExist:
        return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(TaskSerializer(task).data)

    org = _get_approved_org(request.user)
    if not org or task.organisation != org:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PATCH':
        if task.workers_accepted > 0:
            return Response(
                {'detail': 'Cannot edit a task that already has accepted workers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = TaskCreateSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TaskSerializer(task).data)

    task.status = Task.Status.CLOSED
    task.save(update_fields=['status'])
    return Response({'detail': 'Task closed.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_task(request, task_id):
    try:
        task = Task.objects.get(pk=task_id, status=Task.Status.OPEN)
    except Task.DoesNotExist:
        return Response(
            {'detail': 'Task not found or no longer available.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if task.is_full:
        return Response({'detail': 'This task is full.'}, status=status.HTTP_400_BAD_REQUEST)

    if TaskAssignment.objects.filter(task=task, worker=request.user).exists():
        return Response({'detail': 'You have already accepted this task.'}, status=status.HTTP_400_BAD_REQUEST)

    assignment = TaskAssignment.objects.create(task=task, worker=request.user)
    task.workers_accepted += 1
    if task.workers_accepted >= task.workers_needed:
        task.status = Task.Status.IN_PROGRESS
    task.save(update_fields=['workers_accepted', 'status'])

    return Response(
        {'detail': 'Task accepted.', 'assignment_id': assignment.id},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_task(request, task_id):
    try:
        assignment = TaskAssignment.objects.get(
            task_id=task_id, worker=request.user, status=TaskAssignment.Status.ACCEPTED
        )
    except TaskAssignment.DoesNotExist:
        return Response({'detail': 'No active assignment found.'}, status=status.HTTP_404_NOT_FOUND)

    assignment.status = TaskAssignment.Status.WITHDRAWN
    assignment.save(update_fields=['status'])

    task = assignment.task
    task.workers_accepted = max(0, task.workers_accepted - 1)
    if task.status == Task.Status.IN_PROGRESS:
        task.status = Task.Status.OPEN
    task.save(update_fields=['workers_accepted', 'status'])

    return Response({'detail': 'Withdrawn from task.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_tasks(request):
    """Returns assignments in the shape the frontend expects."""
    assignments = (
        TaskAssignment.objects
        .filter(worker=request.user)
        .select_related('task', 'task__organisation')
        .order_by('-accepted_at')
    )
    return Response(MyTaskSerializer(assignments, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def org_dashboard(request):
    org = _get_approved_org(request.user)
    if not org:
        return Response({'detail': 'Approved organisation required.'}, status=status.HTTP_403_FORBIDDEN)

    tasks = Task.objects.filter(organisation=org).prefetch_related('assignments__worker')
    result = []
    for task in tasks:
        result.append({
            'task': TaskSerializer(task).data,
            'assignments': TaskAssignmentSerializer(task.assignments.all(), many=True).data,
        })
    return Response(result)
