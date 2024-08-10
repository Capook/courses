from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django_tex.shortcuts import render_to_pdf
from django.utils import timezone

from .forms import SubmissionForm
from .models import Assignment
from .models import Course
from .models import Registration
from .models import Submission


@login_required
def my_courses(request):
    registrations = Registration.objects.filter(user=request.user)
    context = {
        "registrations": registrations,
    }  # Pass registrations instead of just courses
    return render(request, "selfgrade/my_courses.html", context)


from django.contrib.auth.decorators import login_required


@login_required
def my_courses(request):
    registrations = Registration.objects.filter(user=request.user)
    context = {"registrations": registrations}
    return render(request, "selfgrade/my_courses.html", context)


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course).prefetch_related(
        "assignedproblem_set",
    )
    registration = get_object_or_404(Registration, user=request.user, course=course)

    if request.method == "POST":
        assignment_id = request.POST.get("assignment_id")
        assignment = get_object_or_404(Assignment, id=assignment_id)

        if assignment.due_at < timezone.now():
            return HttpResponseForbidden("Cannot submit after the deadline.")

        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission, created = Submission.objects.get_or_create(
                registration=registration,
                assignment=assignment,
            )
            submission.initial_submission = form.cleaned_data["initial_submission"]
            submission.submitted_at = timezone.now()
            submission.save()
            return redirect("selfgrade:course_detail", course_id=course_id)
    else:
        form = SubmissionForm()

    # Prepare a dictionary to store submissions for each assignment
    submissions = {}
    for assignment in assignments:
        submissions[assignment.id] = registration.submission_set.filter(
            assignment=assignment,
        ).first()

    context = {
        "course": course,
        "assignments": assignments,
        "registration": registration,
        "form": form,
        "submissions": submissions,
    }
    return render(request, "selfgrade/course_detail.html", context)

def testpdf(request):
    template_name = 'selfgrade/tex/test.tex'
    context = {'foo': 'Bar'}
    return render_to_pdf(request, 'selfgrade/tex/test.tex', context, filename='test.pdf')
