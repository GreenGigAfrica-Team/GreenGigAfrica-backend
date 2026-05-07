from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.models import JobSeekerProfile
from apps.tasks.models import TaskAssignment


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def volunteer_impact(request):
    """Return the volunteer's cumulative impact score."""
    try:
        profile = request.user.profile
    except JobSeekerProfile.DoesNotExist:
        return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'full_name': profile.full_name,
        'total_tasks_completed': profile.total_tasks_completed,
        'total_waste_kg': str(profile.total_waste_kg),
        'total_trees_planted': profile.total_trees_planted,
        'total_earnings': str(profile.total_earnings),
        'impact_score': str(profile.impact_score),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_certificate(request, assignment_id):
    """Download PDF certificate for a completed volunteer task."""
    try:
        assignment = TaskAssignment.objects.select_related(
            'task__organisation', 'worker'
        ).get(pk=assignment_id, worker=request.user)
    except TaskAssignment.DoesNotExist:
        return Response({'detail': 'Assignment not found.'}, status=status.HTTP_404_NOT_FOUND)

    if assignment.status != TaskAssignment.Status.APPROVED:
        return Response(
            {'detail': 'Certificate only available after approval.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not assignment.task.is_volunteer_only:
        return Response(
            {'detail': 'Certificates are for volunteer tasks only.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        volunteer_name = request.user.profile.full_name
    except Exception:
        volunteer_name = request.user.phone_number

    pdf_bytes = _generate_certificate(
        volunteer_name=volunteer_name,
        task_title=assignment.task.title,
        org_name=assignment.task.organisation.name,
        completed_date=assignment.reviewed_at,
    )

    from django.http import HttpResponse
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    safe_name = volunteer_name.replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="GreenGig_Certificate_{safe_name}.pdf"'
    return response


def _generate_certificate(volunteer_name, task_title, org_name, completed_date):
    from django.utils import timezone
    try:
        import io
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        green = colors.HexColor('#1a6b3c')
        date_str = completed_date.strftime('%B %d, %Y') if completed_date else timezone.now().strftime('%B %d, %Y')

        center = ParagraphStyle('C', parent=styles['Normal'], alignment=TA_CENTER)
        story = [
            Spacer(1, 0.5*cm),
            Paragraph('<font size=28 color="#1a6b3c"><b>🌿 GreenGig Africa</b></font>', center),
            Paragraph('<font size=14 color="grey">Certificate of Participation</font>', center),
            Spacer(1, 0.3*cm),
            HRFlowable(width='80%', thickness=2, color=green, spaceAfter=20),
            Paragraph('<font size=13>This is to certify that</font>', center),
            Paragraph(f'<font size=24 color="#1a6b3c"><b>{volunteer_name}</b></font>', center),
            Paragraph(f'<font size=13>has successfully completed the volunteer task <b>{task_title}</b></font>', center),
            Paragraph(f'<font size=13>organised by <b>{org_name}</b> on <b>{date_str}</b></font>', center),
            Spacer(1, 1*cm),
            Paragraph('<font size=11 color="grey">Thank you for contributing to a greener Lagos.</font>', center),
            Paragraph('<font size=10 color="#1a6b3c">GreenGig Africa — Clean Green, Earn Clean.</font>', center),
        ]
        doc.build(story)
        return buffer.getvalue()
    except ImportError:
        text = f'CERTIFICATE OF PARTICIPATION\n\n{volunteer_name} completed\n"{task_title}" by {org_name}.\n\nGreenGig Africa'
        return text.encode('utf-8')
