from django.db.models.signals import post_save, pre_delete
from .models import Submission, GradedPart, Problem, AssignedPart, AssignedProblem, Registration, Test, GradedTest
from django.core.exceptions import ValidationError

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
    If assignment is edited AFTER a submission is made, then graded parts will be out of sync with assigned parts.
    This is the intended behavior as the grading should not be modified by a change in the assigned problem.
    Well, I guess it would be better to prevent it.  But that is pretty confusing in django.
    """
    if created:
        submission = instance
        assigned_problems = submission.assignment.assignedproblem_set.all()
        for assigned_problem in assigned_problems:
            assigned_parts = assigned_problem.assignedpart_set.all()
            for assigned_part in assigned_parts:
                graded_part = GradedPart(submission=submission, assigned_part=assigned_part)
                graded_part.save()

post_save.connect(create_graded_parts, sender=Submission)

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
