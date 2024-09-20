from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

import csv

from .forms import SubmissionForm, GradedSubmissionForm, GradingFormSet, ReviewerCommentsForm, ReviewFormSet
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
    if registrations.count() == 1:
        return redirect("selfgrade:course_detail", course_id=registrations.first().course.id)
    context = {"registrations": registrations}
    return render(request, "selfgrade/my_courses.html", context)


@login_required
def course_detail(request, course_id):
    #this could be just registration_detail... right?
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course).order_by('due_at').prefetch_related("assignedproblem_set")
    registration = Registration.objects.filter(user=request.user, course=course).first()
    if not registration:
        return redirect('selfgrade:my_courses')

    # We initialize everything as if it is a get and then overwrite the appropriate form if it's a post
    # This makes sure everything is defined for context at the end
    # Prepare a dictionary of submissions for each assignment associated with this registration
    submissions = {}
    for assignment in assignments:
        submissions[assignment.id] = registration.submission_set.filter(
            assignment=assignment,
        ).first()
        #add formset - assumes GradedParts have been created (automatic at submission creation)
        if submissions[assignment.id]:
            submissions[assignment.id].grading_formset = GradingFormSet(instance=submissions[assignment.id])

    grading_scheme = 'Total is calculated as the average of homework percentages, dropping the two lowest scores.'
    percentage_grades = registration.get_assignment_grades()
    grades = registration.get_grades()

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
        "grades": grades,
        "grading_scheme": grading_scheme,
    }
    return render(request, "selfgrade/course_detail.html", context)

def single_course_view(request):
    if request.user.is_authenticated and request.user.registration_set.count() == 1:
        return redirect("selfgrade:course_detail", course_id=request.user.registration_set.first().course.id)
    else:
        return render(request, "pages/home.html", {})

@staff_member_required
def next_review(request, assignment_id):
    next_submission=Submission.objects.filter(assignment=assignment_id, reviewed_at__isnull=True).first()
    if next_submission:
        return redirect('selfgrade:review', submission_id=next_submission.id)
    else:
        course = Assignment.objects.get(id=assignment_id).course
        return redirect('selfgrade:review_list', course_id=course.id)

@staff_member_required
def review_list(request, course_id):
    submissions=Submission.objects.filter(registration__course=course_id, reviewed_at__isnull=True)
    return render(request,"selfgrade/review_list.html",{'submissions':submissions})

@staff_member_required
def review(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    if request.method == "POST":
        reviewer_comments_form = ReviewerCommentsForm(request.POST, instance=submission)
        review_formset = ReviewFormSet(request.POST, instance=submission)
        #because of my hand-input initial value in the formset constructor, django sometimes thinks that form data
        #has not changed and therefore refuses to save it.  This forces it to change.
        #see https://stackoverflow.com/questions/18355976/django-formset-data-does-not-get-saved-when-initial-values-are-provided
        for form in review_formset.forms:
            form.changed_data = ['grade']
        if reviewer_comments_form.is_valid() and review_formset.is_valid():
            reviewer_comments_form.save()
            review_formset.save()
            submission.reviewed_by = request.user
            submission.reviewed_at = timezone.now()
            submission.save()
            messages.add_message(request, messages.SUCCESS, f'Successfully submitted review: {submission.assignment.name} for {submission.registration.user}')
            return redirect('selfgrade:next_review',assignment_id=submission.assignment.id)
    else:
        reviewer_comments_form = ReviewerCommentsForm(instance=submission)
        review_formset = ReviewFormSet(instance=submission)

    context = {
        "submission": submission,
        "reviewer_comments_form": reviewer_comments_form,
        "review_formset": review_formset,
        "adobe_api_key": settings.ADOBE_EMBED_API_KEY
    }
    return render(request, "selfgrade/review.html", context)

@staff_member_required()
def grade_report(request, course_id):
    registrations = Registration.objects.filter(course_id=course_id)

    headers = []
    data = []
    if registrations:
        for registration in registrations:
            row = [registration.user.email]
            pg = registration.get_assignment_grades()
            row = row + list(pg.values())
            data.append(row)
        headers = ['Email'] + list(pg.keys())

    context = {'headers': headers, 'data': data} #django template logic is limited... pass keys here

    return render(request,"selfgrade/grade_report.html", context )

@staff_member_required()
def assignment_grades_csv(request, course_id):
    registrations = Registration.objects.filter(course_id=course_id)

    headers = []
    data = []
    if registrations:
        for registration in registrations:
            row = [registration.user.last_name, registration.user.first_name, registration.user.email]
            pg = registration.get_assignment_grades()
            row = row + list(pg.values())
            data.append(row)
        headers = ['Last name', 'First name', 'Email'] + list(pg.keys())

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="output.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(data)

    return response

def grading_instructions(request):
    return render(request, "selfgrade/grading_instructions.html", {})
