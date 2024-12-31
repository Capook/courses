from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST
from django.utils.safestring import mark_safe

import csv

from .forms import SubmissionForm, GradedSubmissionForm, GradingFormSet, ReviewerCommentsForm, ReviewFormSet, \
    MaterialForm, AssignmentForm, CourseNameForm, CourseDescriptionForm, PartFormSet
from .models import Assignment, Course, Registration, Submission, Material, Part


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
        return redirect("selfgrade:course", course_id=registrations.first().course.id)
    context = {"registrations": registrations}
    return render(request, "selfgrade/my_courses.html", context)


@login_required
def course_detail(request, course_id):
    #this could be just registration_detail... right?
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course).order_by('due_at').prefetch_related("assignedproblem_set")
    materials = Material.objects.filter(course=course)
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

    assignment_grading_scheme = 'Total is calculated as the average of homework percentages, dropping the two lowest scores.'
    percentage_grades = registration.get_assignment_grades() #assignment grades
    grading_scheme = 'Total is calculated as the weighted average: Assignments 20%, quizzes each 5%, midterm 25%, final 30%.  You are guaranteed to receive an A/B/C/D if your total is at least 85/70/60/50.'
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
                return redirect("selfgrade:course", course_id=course_id)

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
                return redirect('selfgrade:course', course_id=course_id)
            else:
                submissions[assignment.id].grading_formset = grading_formset
                #need to overwrite this since we pass the formset in this weird way

    context = {
        "course": course,
        "assignments": assignments,
        "registration": registration,
        "submission_form": submission_form,
        "graded_submission_form": graded_submission_form,
        "submissions": submissions,
        "percentage_grades": percentage_grades,
        "grades": grades,
        "assignment_grading_scheme": assignment_grading_scheme,
        "grading_scheme": grading_scheme,
        "materials": materials
    }
    return render(request, "selfgrade/course_detail.html", context)

#get all assignments for a given registration and add forms necessary for template
#some code duplication with add_submission for queryset efficiency
def get_assignments(registration):
    # get all assignments and materials for the course
    assignments = Assignment.objects.filter(course=registration.course).prefetch_related("part_set")

    # get all submissions by this user and attach to each assignment (or None if not submitted), including relevant forms
    submissions = Submission.objects.filter(registration=registration)
    for assignment in assignments:
        assignment.form = AssignmentForm(instance=assignment)
        assignment.formset = PartFormSet(instance=assignment)
        assignment.parts = assignment.part_set.all()  # makes the parts template-accessible

        assignment.submission = submissions.filter(assignment=assignment).first()  # none if object doesn't exist
        if assignment.submission:
            assignment.graded_submission_form = GradedSubmissionForm(instance=assignment.submission)
            assignment.grading_formset = GradingFormSet(instance=assignment.submission)
            assignment.submission_form = SubmissionForm(instance=assignment.submission)
        else:
            # make sure blank submission form knows what assignment
            assignment.submission_form = SubmissionForm(
                initial={"assignment": assignment, "registration": registration})

    return assignments


#add some submission forms to the object assignment for object registration
#some code duplication with get_assignments for queryset efficiency
def add_submission(assignment, registration):
    assignment.submission = Submission.objects.filter(assignment=assignment).first() #none if not present
    if assignment.submission:
        assignment.graded_submission_form = GradedSubmissionForm(instance=assignment.submission)
        assignment.grading_formset = GradingFormSet(instance=assignment.submission)
        assignment.submission_form = SubmissionForm(instance=assignment.submission)
    else:
        # make sure blank submission form knows what assignment
        assignment.submission_form = SubmissionForm(initial={"assignment": assignment, "registration": registration})


############################ main page views ##########################

@login_required
def grading(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    registration = get_object_or_404(Registration, course=course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Permission denied')

    submissions = Submission.objects.filter(registration__course=course_id,
                                            registration__type=Registration.STUDENT,
                                            reviewed_at__isnull=True)

    context = {"instructor": True, "course": course, "submissions": submissions}
    return render(request, "selfgrade/grading.html", context)

@login_required
def course(request, course_id):
    #make sure course exists and user is registered
    course = get_object_or_404(Course, id=course_id)
    registration = get_object_or_404(Registration,course=course,user=request.user)
    instructor = registration.type == Registration.INSTRUCTOR

    #materials
    materials = Material.objects.filter(course=course)
    create_material_form = MaterialForm(initial={"course": course})
    for material in materials:
        material.form = MaterialForm(instance=material)

    #assignments
    assignments = get_assignments(registration)
    create_assignment_form = AssignmentForm(initial={"course": course})

    #grades
    assignment_grading_scheme = 'Total is calculated as the average of homework percentages, dropping the two lowest scores.'
    percentage_grades = registration.get_assignment_grades()  # assignment grades
    grading_scheme = 'Total is calculated as the weighted average: Assignments 20%, quizzes each 5%, midterm 25%, final 30%.  You are guaranteed to receive an A/B/C/D if your total is at least 85/70/60/50.'
    grades = registration.get_grades()

    context = {
        "course": course,
        "assignments": assignments,
        "create_assignment_form": create_assignment_form,
        "materials": materials,
        "create_material_form": create_material_form,
        "course_name_update_form": CourseNameForm(instance=course),
        "course_description_update_form": CourseDescriptionForm(instance=course),
        "percentage_grades": percentage_grades,
        "grades": grades,
        "assignment_grading_scheme": assignment_grading_scheme,
        "grading_scheme": grading_scheme,
        "instructor": instructor #enable editing - add this elsewhere!
    }
    return render(request, "selfgrade/course.html", context)

############################## COURSE CRUD ###########################################

@require_POST
def update_course_name(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    registration = get_object_or_404(Registration, course=course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Permission denied')

    course_name_update_form = CourseNameForm(request.POST, instance=course)
    if course_name_update_form.is_valid():
        course_name_update_form.save()

    return render(request, "selfgrade/course.html#name",
                  {"course": course,
                   "course_name_update_form": course_name_update_form,
                   "instructor": True})

def update_course_description(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    registration = get_object_or_404(Registration, course=course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Permission denied')

    if request.method == 'POST':
        course_description_update_form = CourseDescriptionForm(request.POST, instance=course)
        if course_description_update_form.is_valid():
            course_description_update_form.save()

    return render(request, "selfgrade/course.html#description",
                  {"course": course,
                   "course_description_update_form": course_description_update_form,
                   "instructor": True})

############################## ASSIGNMENTS AND PARTS CRUD (INSTRUCTOR REQUIRED) #######################################

@require_POST
def reorder_assignments(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    registration = get_object_or_404(Registration, course=course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Forbidden')
    item = int(request.POST['item'])
    position = int(request.POST['position'])
    Assignment.objects.get(pk=item).to(position) #update ordering

    #refetch everything
    assignments=get_assignments(registration)
    create_assignment_form = AssignmentForm(initial={"course": course})

    return render(request, "selfgrade/course.html#assignments",
                  {"course": course, "assignments": assignments,
                   "create_assignment_form": create_assignment_form,
                   "instructor": True})

@require_POST
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    registration = get_object_or_404(Registration, course=assignment.course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Forbidden')
    if assignment.submission_set.exists():
        assignment.form = AssignmentForm(instance=assignment)
        assignment.formset = PartFormSet(instance=assignment)
        assignment.parts = assignment.part_set.all()
        add_submission(assignment, registration)
        assignment.delete_forbidden = True
        return render(request, "selfgrade/course.html#assignment",
                      {"assignment": assignment, "instructor": True})

    assignment.delete()
    return render(request, "selfgrade/course.html#deleted_assignment",
                  {"assignment": assignment,"instructor": True})
    #return HttpResponse(mark_safe('<div class="alert alert-success alert-dismissible fade show">Assignment deleted</div>')) #any message here woudl be shown instead of the old div

@require_POST
def update_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    registration = get_object_or_404(Registration, course=assignment.course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Forbidden')

    assignment_form = AssignmentForm(request.POST, request.FILES, instance=assignment)
    if assignment_form.is_valid():
        assignment_form.save()
        assignment_form = AssignmentForm(instance=assignment)  # reinitialize to get files to match

    assignment.formset = PartFormSet(instance=assignment) #this will overwrite any changes to their partformset, but necessary since we replace the whole thing
    assignment.form = assignment_form
    assignment.parts = assignment.part_set.all()
    add_submission(assignment, registration)
    return render(request, "selfgrade/course.html#assignment",
                      {"assignment": assignment,"instructor": True})

@require_POST
def create_assignment(request):
    create_assignment_form = AssignmentForm(request.POST, request.FILES)
    course_id = int(create_assignment_form.data['course'])
    course = get_object_or_404(Course, id=course_id)
    registration = get_object_or_404(Registration, course=course_id, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Forbidden')

    if create_assignment_form.is_valid():
        create_assignment_form.save()
        create_assignment_form = AssignmentForm(initial={"course": course})

    assignments = course.assignment_set.all().prefetch_related("part_set")
    for assignment in assignments:
        assignment.form = AssignmentForm(instance=assignment)
        assignment.formset = PartFormSet(instance=assignment)
        assignment.parts = assignment.part_set.all()
        add_submission(assignment, registration)

    return render(request, "selfgrade/course.html#assignments",
                      {"course": course, "assignments": assignments,
                       "create_assignment_form": create_assignment_form, "instructor": True})


@require_POST
def update_parts(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    registration = get_object_or_404(Registration, course=assignment.course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Permission denied')

    assignment_formset = PartFormSet(request.POST, instance=assignment)
    if assignment_formset.is_valid():
        assignment_formset.save()
        assignment_formset = PartFormSet(instance=assignment)
        #reinitalize in case anything was deleted

    assignment.form = AssignmentForm(instance=assignment)
    assignment.formset = assignment_formset
    assignment.parts = assignment.part_set.all()
    add_submission(assignment, registration)
    return render(request, "selfgrade/course.html#assignment",
                      {"assignment": assignment, "instructor": True})

############################## SUBMISSIONS ###########################################

@require_POST
def submit_assignment(request):
    submission_form = SubmissionForm(request.POST, request.FILES)
    assignment_id = int(submission_form.data['assignment'])
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    registration_id = int(submission_form.data['registration'])
    registration = get_object_or_404(Registration, pk=registration_id)
    instructor = registration.type == Registration.INSTRUCTOR

    if registration.course != assignment.course:
        return HttpResponseForbidden("Invalid registration.")
    if assignment.due_at < timezone.now():
        return HttpResponseForbidden("Cannot submit after the deadline.")

    #we want to update submission if it already exists
    submission = Submission.objects.filter(assignment=assignment_id,registration=registration_id).first()
    if submission:
        submission_form = SubmissionForm(request.POST, request.FILES, instance=submission)

    success = False
    if submission_form.is_valid():
        submission = submission_form.save(commit=False)
        submission.submitted_at = timezone.now()
        submission.save()
        success = True
        submission_form = SubmissionForm(instance=submission_form.instance)  # reinitialize to get files to match - is this necessary?

    #just replace submission, but it expects assignment
    assignment.submission = submission_form.instance
    assignment.submission_form = submission_form
    assignment.submission.success = success
    return render(request, "selfgrade/course.html#submission",
                      {"assignment": assignment, "instructor": instructor})


@require_POST
def submit_grading(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    registration = submission.registration
    if request.user != registration.user:
        return HttpResponseForbidden("Permission denied")
    instructor = registration.type == Registration.INSTRUCTOR

    assignment = submission.assignment
    grading_formset = GradingFormSet(request.POST, instance=submission)
    graded_submission_form =  GradedSubmissionForm(request.POST, request.FILES, instance=submission)
    success = False
    if grading_formset.is_valid() and graded_submission_form.is_valid():
        grading_formset.save()
        submission = graded_submission_form.save(commit=False)
        submission.graded_at = timezone.now()
        submission.save()
        success = True

    assignment.submission = submission
    assignment.grading_formset = grading_formset
    assignment.graded_submission_form = graded_submission_form
    assignment.submission.grading_success = success
    return render(request, "selfgrade/course.html#grading",
                  {"assignment": assignment, "instructor": instructor})

######################## MATERIALS ########################

@require_POST
def reorder_materials(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    #TODO CHECK PERSON IS INSTRUCTOR
    item = int(request.POST['item'])
    position = int(request.POST['position'])
    Material.objects.get(pk=item).to(position) #update ordering
    materials = course.material_set.all()  # we will need all the materials
    for material in materials:
        material.form = MaterialForm(instance=material)
    create_material_form = MaterialForm(initial={"course": course})
    return render(request, "selfgrade/course.html#materials",
                  {"course": course, "materials": materials,
                   "create_material_form": create_material_form, "instructor": True})

@require_POST
def delete_material(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    #TODO owner check
    material.delete()
    return HttpResponse('')

@require_POST
def update_material(request, material_id):
    #TODO check that this person owns the relevant course (course is stored in POST request)
    material = get_object_or_404(Material, id=material_id)
    material_form = MaterialForm(request.POST, request.FILES, instance=material)
    if material_form.is_valid():
        material_form.save()
        material_form = MaterialForm(instance=material) #reinitialize to get file to match

    material.form = material_form
    return render(request, f"selfgrade/course.html#material",
                      {"material": material,"instructor": True})

@require_POST
def create_material(request):
    #TODO check that this person owns the relevant course (course is stored in POST request)
    create_material_form = MaterialForm(request.POST, request.FILES)
    course_id = int(create_material_form.data['course'])
    course = get_object_or_404(Course, pk=course_id) #should change this for better error-handling
    if create_material_form.is_valid():
        create_material_form.save()
        create_material_form = MaterialForm(initial={"course": course}) #reinitialize to get file to match

    materials = course.material_set.all()
    for material in materials:
        material.form = MaterialForm(instance=material)

    return render(request, "selfgrade/course.html#materials",
                      {"course": course, "materials": materials,
                       "create_material_form": create_material_form, "instructor": True})

def single_course_view(request):
    if request.user.is_authenticated and request.user.registration_set.count() == 1:
        return redirect("selfgrade:course", course_id=request.user.registration_set.first().course.id)
    else:
        return render(request, "pages/home.html", {})

@login_required
def next_review(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    registration = get_object_or_404(Registration, course=assignment.course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Permission denied')

    #Show the next submission to review
    unreviewed_submissions = Submission.objects.filter(assignment=assignment_id,
                                                       reviewed_at__isnull=True,
                                                       registration__type=Registration.STUDENT)
    next_submission = unreviewed_submissions.exclude(graded_submission='').first()
    if next_submission:
        return redirect('selfgrade:review', submission_id=next_submission.id)
    else:
        #If there are no graded submissions to review, show us any who submitted the hw but not the grading
        next_nonsubmission = unreviewed_submissions.first()
        if next_nonsubmission:
            return redirect('selfgrade:review', submission_id=next_nonsubmission.id)

        #We've reviewed all the submissions, so redirect elsewhere
        course = Assignment.objects.get(id=assignment_id).course
        return redirect('selfgrade:grading', course_id=course.id)

@login_required
def review_list(request, course_id):
    registration = get_object_or_404(Registration, course=course_id, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Permission denied')

    submissions = Submission.objects.filter(registration__course=course_id,
                                            registration__type=Registration.STUDENT,
                                            reviewed_at__isnull=True)

    return render(request,"selfgrade/review_list.html",{'submissions':submissions})

@login_required
def review(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    registration = get_object_or_404(Registration, course=submission.assignment.course, user=request.user)
    if registration.type != Registration.INSTRUCTOR:
        return HttpResponseForbidden('Permission denied')

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

@login_required
def assignment_grade_report(request, course_id):
    if not request.user.is_staff:
        registration = Registration.objects.filter(user=request.user,course=course_id,type=Registration.INSTRUCTOR).first()
        if not registration:
            return HttpResponseForbidden('permission denied')

    registrations = Registration.objects.filter(course_id=course_id)

    headers = []
    data = []
    if registrations:
        for registration in registrations:
            row = [registration.user.name, registration.user.email]
            pg = registration.get_assignment_grades()
            row = row + list(pg.values())
            data.append(row)
        headers = ['Name', 'Email'] + list(pg.keys())

    context = {'headers': headers, 'data': data} #django template logic is limited... pass keys here

    return render(request,"selfgrade/assignment_grade_report.html", context )


@login_required
def assignment_grade_table(request, course_id):
    if not request.user.is_staff:
        registration = Registration.objects.filter(user=request.user,course=course_id,type=Registration.INSTRUCTOR).first()
        if not registration:
            return HttpResponseForbidden('permission denied')

    registrations = Registration.objects.filter(course_id=course_id,type=Registration.STUDENT)

    headers = []
    data = []
    if registrations:
        for registration in registrations:
            row = [registration.user.name, registration.user.email]
            pg = registration.get_assignment_grades()
            row = row + list(pg.values())
            data.append(row)
        headers = ['Name', 'Email'] + list(pg.keys())

    context = {'headers': headers, 'data': data} #django template logic is limited... pass keys here

    return render(request, "selfgrade/data_table.html", context)

@login_required
def grade_report(request, course_id):
    if not request.user.is_staff:
        registration = Registration.objects.filter(user=request.user,course=course_id,type=Registration.INSTRUCTOR).first()
        if not registration:
            return HttpResponseForbidden('permission denied')

    registrations = Registration.objects.filter(course_id=course_id)

    headers = []
    data = []
    if registrations:
        for registration in registrations:
            row = [registration.user.name, registration.user.email]
            pg = registration.get_grades()
            row = row + list(pg.values())
            data.append(row)
        headers = ['Name', 'Email'] + list(pg.keys())

    context = {'headers': headers, 'data': data} #django template logic is limited... pass keys here

    return render(request,"selfgrade/grade_report.html", context )

@login_required
def assignment_grades_csv(request, course_id):
    if not request.user.is_staff:
        registration = Registration.objects.filter(user=request.user,course=course_id,type=Registration.INSTRUCTOR).first()
        if not registration:
            return HttpResponseForbidden('permission denied')

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
