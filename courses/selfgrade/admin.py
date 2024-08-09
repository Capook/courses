from django.contrib import admin

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


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("name", "topic")
    list_filter = ("topic",)
    search_fields = ("name", "notes")
    inlines = [PartInline]


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


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "due_at")
    list_filter = ("course",)
    search_fields = ("name",)
    inlines = [AssignedProblemInline]


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
