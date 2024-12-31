from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from .models import Submission, GradedPart, Problem, AssignedPart, Part, AssignedProblem, Registration, Test, GradedTest, Assignment
from django.core.exceptions import ValidationError
from django.dispatch import receiver

def create_generic_problem(sender, instance, created, **kwargs):
    if created:
        assignment = instance


post_save.connect(create_generic_problem, sender=Assignment)

def create_assigned_parts(sender, instance, created, **kwargs):
    """
    Create assigned parts when assignedproblem object is created - using default point value
    """
    if created:
        assigned_problem = instance
        num_parts = assigned_problem.problem.num_parts
        for i in range(num_parts):
            AssignedPart.objects.create(assigned_problem=assigned_problem,number=i+1)


post_save.connect(create_assigned_parts, sender=AssignedProblem)

def create_graded_parts(sender, instance, created, **kwargs):
    """
    Create graded parts when submission object is created.
    """
    if created:
        submission = instance
        parts = submission.assignment.part_set.all()
        for part in parts:
            graded_part = GradedPart(submission=submission, part=part)
            graded_part.save()

post_save.connect(create_graded_parts, sender=Submission)

@receiver(pre_save, sender=Part)
def store_original_schema(sender, instance, **kwargs):
    instance.original_schema = instance.schema

@receiver(post_save, sender=Part)
def update_graded_parts(sender, instance, created, **kwargs):
    """
    reset grade if schema changes
    """
    #if a new part is added, create a new graded part for all submissions
    part = instance
    schema_changed = part.original_schema and part.schema != part.original_schema

    if created:
        #if it's a new part, great a new graded part for each submission
        submissions = part.assignment.submission_set.all()
        for submission in submissions:
            graded_part = GradedPart(submission=submission, part=part)
            graded_part.save()
        #if it's an update, reset the score for any schema change
    elif schema_changed:
        graded_parts = GradedPart.objects.filter(part=part)
        for graded_part in graded_parts:
            graded_part.self_grade = None
            graded_part.grade = None

#no need for post-delete since cascade

def create_graded_tests(sender, instance, created, **kwargs):
    """
    Create graded tests when a Test object is created
    """
    if created:
        for registration in Registration.objects.filter(course=instance.course):
            GradedTest.objects.create(registration=registration, test=instance)

post_save.connect(create_graded_tests, sender=Test)

def create_graded_tests_for_user(sender, instance, created, **kwargs):
    """
    Create graded tests when a student is registered
    """
    if created:
        for test in Test.objects.filter(course=instance.course):
            GradedTest.objects.create(registration=instance, test=test)

post_save.connect(create_graded_tests_for_user, sender=Registration)
