from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import AssignedProblem
from .models import Assignment
from .models import Course
from .models import GradedPart
from .models import Part
from .models import Problem
from .models import Registration
from .models import Submission
from .models import Topic

# Register your models here.


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    list_filter = ("parent",)
    search_fields = ("name",)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("problem", "number")
    list_filter = ("problem",)


class PartInline(admin.TabularInline):
    model = Part
    extra = 1  # Number of extra empty forms to display initially

@admin.action(description='Compile tex')
def compile_problem_tex_action(modeladmin, request, queryset):
    for problem in queryset:
        problem.compile_statement()
        problem.compile_solution()

    modeladmin.message_user(request, 'PDFs saved successfully.')
    return HttpResponseRedirect(reverse('admin:selfgrade_problem_changelist'))  # Redirect back to the changelist view

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("name", "topic")
    list_filter = ("topic",)
    search_fields = ("name", "notes")
    inlines = [PartInline]
    actions = [compile_problem_tex_action]


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    inlines = [RegistrationInline]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "course")
    list_filter = ("user", "course")


class AssignedProblemInline(admin.TabularInline):
    model = AssignedProblem
    extra = 1

@admin.action(description='Compile tex')
def compile_assignment_tex_action(modeladmin, request, queryset):
    for assignment in queryset:
        assignment.compile_statement()
        assignment.compile_solution()

    modeladmin.message_user(request, 'PDFs saved successfully.')
    return HttpResponseRedirect(reverse('admin:selfgrade_assignment_changelist'))  # Redirect back to the changelist view

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "due_at")
    list_filter = ("course",)
    search_fields = ("name",)
    inlines = [AssignedProblemInline]
    actions = [compile_assignment_tex_action]


@admin.register(AssignedProblem)
class AssignedProblemAdmin(admin.ModelAdmin):
    list_display = ("problem", "assignment", "number")
    list_filter = ("assignment", "problem")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "registration",
        "assignment",
        "submitted_at",
        "graded_at",
        "reviewed_at",
    )
    list_filter = (
        "registration__user",
        "assignment",
        "submitted_at",
        "graded_at",
        "reviewed_at",
    )


@admin.register(GradedPart)
class GradedPartAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "part",
        "self_grade",
        "grade_guess",
        "guess_confidence",
        "grade",
    )
    list_filter = (
        "submission__registration__user",
        "submission__assignment",
        "part__problem",
    )
