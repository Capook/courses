from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from ordered_model.admin import OrderedModelAdmin, OrderedTabularInline, OrderedInlineModelAdminMixin

from .models import AssignedProblem
from .models import AssignedPart
from .models import Assignment
from .models import Course
from .models import GradedPart
from .models import Part
from .models import Problem
from .models import Registration
from .models import Submission
from .models import Topic
from .models import Test
from .models import GradedTest
from .models import Material
from .models import Schema
from .models import SchemaItem
from .models import Part

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

    modeladmin.message_user(request, 'PDFs saved.  Logs probably under /static/texput.log')
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

class TestInline(admin.TabularInline):
    model = Test
    extra = 1

class MaterialInline(OrderedTabularInline):
    model = Material
    extra = 1
    fields = ('name','order',) #move_up_down_links doesn't seem to work
    readonly_fields = ('order',)
    ordering=('order',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    model=Course
    list_display = ("name", "description")
    search_fields = ("name", "description")
    inlines = [RegistrationInline, TestInline, MaterialInline]


class GradedTestInline_forregistration(admin.TabularInline):
    model = GradedTest
    extra = 0
    max_num = 0 # no new objects
    can_delete = False
    fields = ('test_name', 'points', 'max')
    readonly_fields = ('test_name', 'max')
    ordering = ('registration__user__name',)

    def max(self, obj):
        return obj.test.max_points

    def test_name(self, obj):
        return obj.test.name

@admin.register(Material)
class MaterialAdmin(OrderedModelAdmin):
    list_display = ('name', 'course','move_up_down_links')

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "course")
    list_filter = ("user", "course")
    inlines = (GradedTestInline_forregistration,)

class AssignedProblemInline(admin.TabularInline):
    model = AssignedProblem
    extra = 1

class PartInline(OrderedTabularInline):
    model = Part
    extra = 1

@admin.action(description='Compile tex')
def compile_assignment_tex_action(modeladmin, request, queryset):
    for assignment in queryset:
        assignment.compile_statement()
        assignment.compile_solution()

    modeladmin.message_user(request, 'PDFs saved.  Logs probably under /static/texput.log')
    return HttpResponseRedirect(reverse('admin:selfgrade_assignment_changelist'))  # Redirect back to the changelist view

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "due_at")
    list_filter = ("course",)
    search_fields = ("name",)
    inlines = [AssignedProblemInline,PartInline]
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

class GradedTestInline_fortest(admin.TabularInline):  # Or admin.StackedInline for a vertical layout
    model = GradedTest
    extra = 0
    max_num = 0 # no new objects
    can_delete = False
    fields = ('student', 'points', 'max')
    readonly_fields = ('student', 'max')
    ordering = ('registration__user__name',)

    def student(self, obj):
        return obj.registration.user.name

    student.short_description = 'Student' #title shown in admin

    def max(self, obj):
        return obj.test.max_points

    def test_name(self, obj):
        return obj.test.name

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    inlines = [GradedTestInline_fortest]

@admin.register(GradedTest)
class GradedTestAdmin(admin.ModelAdmin):
    pass

class SchemaItemInline(admin.TabularInline):
    model = SchemaItem
    extra = 1

@admin.register(Schema)
class AssignedProblemAdmin(admin.ModelAdmin):
    inlines = [SchemaItemInline]

class SchemaItemInline(admin.TabularInline):
    model = SchemaItem
    extra = 1

@admin.register(Part)
class AssignedProblemAdmin(admin.ModelAdmin):
    pass
