from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django_tex.shortcuts import render_to_pdf
from django.utils import timezone
from django.contrib import messages

from .forms import SubmissionForm, GradedSubmissionForm, GradingFormSet
from .models import Assignment, AssignedProblem
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
    if registrations.count() == 1:
        return redirect("selfgrade:course_detail", course_id=registrations.first().course.id)
    context = {"registrations": registrations}
    return render(request, "selfgrade/my_courses.html", context)


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course).order_by('due_at').prefetch_related("assignedproblem_set")
    #assignments = Assignment.objects.filter(course=course).prefetch_related(Prefetch("assignedproblem_set",queryset=AssignedProblem.objects.order_by("number")))
    registration = get_object_or_404(Registration, user=request.user, course=course)

    # We initialize everything as if it is a get and then overwrite the appropriate form if it's a post
    # This makes sure everything is defined for context at the end
    # Prepare a dictionary of submissions for each assignment associated with this registration
    # Also a dictionary of percentage_grades for each assignment (None for ungraded)
    submissions = {}
    percentage_grades = {}
    for assignment in assignments:
        submissions[assignment.id] = registration.submission_set.filter(
            assignment=assignment,
        ).first()
        percentage_grade = None #overwrite if there is one
        #add formset - assumes GradedParts have been created (automatic at submission creation)
        if submissions[assignment.id]:
            submissions[assignment.id].grading_formset = GradingFormSet(instance=submissions[assignment.id])
            percentage_grade = submissions[assignment.id].get_percentage_grade()
        percentage_grades[assignment.name] = percentage_grade
    numeric_percentage_grades = [float(value) for value in percentage_grades.values() if value]
    if numeric_percentage_grades:
        percentage_grades['Total']=sum(numeric_percentage_grades)/len(numeric_percentage_grades)
    else:
        percentage_grades['Total']='--'
    grading_scheme = 'Total is calculated as equally weighted average of homework percentages, dropping two lowest scores'

    #this was Gemini's idea to have one generic form
    #template renders one for each assignment, adding assignment_id.
    #The annoying thing is it doesn't have a 'default value'
    #I would like to use javascript to make it required if there wasn't a previous file
    #But actually all the copies of this file element have the same id... it's crazy annoying
    #There is really no way to certain ones required.  so leave optional
    submission_form = SubmissionForm()
    graded_submission_form = GradedSubmissionForm()

    if request.method == "POST":
        assignment_id_str = request.POST.get("assignment_id")
        assignment = get_object_or_404(Assignment, id=assignment_id_str)
        if 'submission_form_submit' in request.POST:
            if assignment.due_at < timezone.now():
                return HttpResponseForbidden("Cannot submit after the deadline.")
            submission_form = SubmissionForm(request.POST, request.FILES)
            if submission_form.is_valid():
                submission, created = Submission.objects.get_or_create(
                    registration=registration,
                    assignment=assignment,
                )
                submission.initial_submission = submission_form.cleaned_data["initial_submission"]
                submission.submitted_at = timezone.now()
                submission.save()
                messages.add_message(request, messages.SUCCESS, 'Submission successful')
                return redirect("selfgrade:course_detail", course_id=course_id)

        if 'grading_form_submit' in request.POST:
            grading_formset = GradingFormSet(request.POST, request.FILES, instance=submissions[assignment.id])
            graded_submission_form = GradedSubmissionForm(request.POST, request.FILES, instance=submissions[assignment.id])
            # If there isn't a file already (yes validation msut be done here because the form doesn't know the instance)
            if not submissions[assignment.id].graded_submission and not graded_submission_form['graded_submission'].data:
                graded_submission_form.add_error('graded_submission', "Please upload a file.")

            if grading_formset.is_valid() and graded_submission_form.is_valid():
                grading_formset.save()
                graded_submission_form.save()
                graded_submission_form.instance.graded_at = timezone.now()
                graded_submission_form.instance.save()
                messages.add_message(request, messages.SUCCESS, 'Grading submission successful')
                return redirect('selfgrade:course_detail', course_id=course_id)
            else:
                submissions[assignment.id].grading_formset = grading_formset
                #need to overwrite this since we pass the formset in in this weird way

    context = {
        "course": course,
        "assignments": assignments,
        "registration": registration,
        "submission_form": submission_form,
        "graded_submission_form": graded_submission_form,
        "submissions": submissions,
        "percentage_grades": percentage_grades,
        "grading_scheme": grading_scheme,
    }
    return render(request, "selfgrade/course_detail.html", context)

def single_course_view(request):
    if request.user.is_authenticated and request.user.registration_set.count()==1:
        return redirect("selfgrade:course_detail", course_id=request.user.registration_set.first().id)
    else:
        return render(request, "pages/home.html", {})
