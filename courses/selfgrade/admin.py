from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import AssignedProblem
from .models import AssignedPart
from .models import Assignment
from .models import Course
from .models import GradedPart
from .models import Problem
from .models import Registration
from .models import Submission
from .models import Topic

from django.utils.html import format_html

# Register your models here.

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    list_filter = ("parent",)
    search_fields = ("name",)

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


class AssignedPartInline(admin.TabularInline):
    model = AssignedPart
    extra = 0  # Don't allow creation or deletion
    can_delete = False
    max_num = 0

@admin.register(AssignedProblem)
class AssignedProblemAdmin(admin.ModelAdmin):
    list_display = ("problem", "assignment", "number")
    list_filter = ("assignment", "problem")
    inlines = [AssignedPartInline]

class GradedPartInline(admin.TabularInline):
    model = GradedPart
    extra = 0  # Don't allow creation or deletion
    can_delete = False
    max_num = 0

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "registration",
        "assignment",
        "submitted_at",
        "graded_at",
        "reviewed_at",
        "review_link"
    )
    list_filter = (
        "registration__user",
        "assignment",
        "submitted_at",
        "graded_at",
        "reviewed_at",
    )
    inlines = [GradedPartInline]

    def review_link(self, obj):
        url = reverse('selfgrade:review', args=[obj.id])  # Replace 'app_name' with your actual app name
        return format_html('<a href="{}" target="_blank">Review</a>', url)

    review_link.short_description = 'Review'  # Set a column header

@admin.register(AssignedPart)
class AssignedPartAdmin(admin.ModelAdmin):
    list_display = (
        "assigned_problem",
        "number",
        "points",
    )

@admin.register(GradedPart)
class GradedPartAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "assigned_part",
        "self_grade",
        "grade",
    )
    list_filter = (
        "submission__registration__user",
        "submission__assignment",
        "assigned_part__assigned_problem",
    )
