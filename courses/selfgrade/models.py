from django.db import models
from django.core.files.base import ContentFile
from django_tex.core import compile_template_to_pdf
from django.conf import settings

from courses.users.models import User


class Topic(models.Model):
    """
    Represents a topic in a hierarchical structure (tree).
    """

    name = models.CharField(max_length=100, help_text="The name of the topic.")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        help_text="The parent topic, if any. Null for root topics.",
    )

    def __str__(self):
        return self.name


class Problem(models.Model):
    """
    Represents a problem with a statement, solution, and other details.
    """

    name = models.CharField(
        max_length=100,
        help_text="The name or title of the problem.",
    )
    statement_tex = models.TextField(
        help_text="LaTeX source for the problem statement.",
    )
    solution_tex = models.TextField(
        help_text="LaTeX source for the problem solution.",
    )
    statement_pdf = models.FileField(
        blank=True,
        upload_to="problem_statements/",
        help_text="PDF file containing the problem statement.",
    )
    solution_pdf = models.FileField(
        blank=True,
        upload_to="problem_solutions/",
        help_text="PDF file containing the problem solution.",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The topic this problem belongs to.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or comments about the problem.",
    )

    def __str__(self):
        return self.name

    def compile_statement(self):
        """
        Compile the statement tex and save to the statement_pdf field.  No latex error handling atm.
        """
        template_name = 'selfgrade/tex/problem_statement.tex'
        context = {'problem': self, 'aux_absolute_path': settings.LATEX_AUX_FILE}
        pdf_bytes = compile_template_to_pdf(template_name, context)
        content_file = ContentFile(pdf_bytes)
        self.statement_pdf.save(
            f"problem_{self.id}_statement.pdf", content_file
        )
        self.save()

    def compile_solution(self):
        """
        Compile the solution tex and save to the solution_pdf field.  No latex error handling atm.
        """
        template_name = 'selfgrade/tex/problem_solution.tex'
        context = {'problem': self, 'aux_absolute_path': settings.LATEX_AUX_FILE}
        pdf_bytes = compile_template_to_pdf(template_name, context)
        content_file = ContentFile(pdf_bytes)
        self.solution_pdf.save(
            f"problem_{self.id}_solution.pdf", content_file
        )
        self.save()


class Part(models.Model):
    """
    Represents the existence of a part or sub-problem within a problem.
    """

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="parts",
        help_text="The problem this part belongs to.",
    )
    number = models.PositiveIntegerField(
        help_text="The order of this part within the problem.",
    )

    class Meta:
        unique_together = ("problem", "number")

    def __str__(self):
        return f"Part {self.number} of {self.problem}"


class Course(models.Model):
    """
    Represents a course with a name and description.
    """

    name = models.CharField(max_length=100, help_text="The name of the course.")
    description = models.TextField(
        blank=True,
        help_text="A description of the course content.",
    )

    def __str__(self):
        return self.name


class Registration(models.Model):
    """
    Represents a user's registration in a course.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The user who is registered.",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        help_text="The course the user is registered in.",
    )

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} registered in {self.course}"


class Assignment(models.Model):
    """
    Represents an assignment given in a course.
    """

    due_at = models.DateTimeField(help_text="The date and time the assignment is due.")
    name = models.CharField(
        max_length=100,
        help_text="The name or title of the assignment.",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        help_text="The course this assignment belongs to.",
    )
    statement_pdf = models.FileField(
        blank=True,
        upload_to="assignment_statements/",
        help_text="PDF file containing the assignment statement.",
    )
    solution_pdf = models.FileField(
        blank=True,
        upload_to="assignment_solutions/",
        help_text="PDF file containing the assignment solution.",
    )

    def __str__(self):
        return f"{self.name} (due {self.due_at}) for {self.course}"

    def compile_statement(self):
        """
        Compile the statement tex and save to the statement_pdf field.  No latex error handling atm.
        """
        template_name = 'selfgrade/tex/assignment_statement.tex'
        context = {'assignment': self, 'aux_absolute_path': settings.LATEX_AUX_FILE}
        pdf_bytes = compile_template_to_pdf(template_name, context)
        content_file = ContentFile(pdf_bytes)
        self.statement_pdf.save(
            f"assignment_{self.id}_statement.pdf", content_file
        )
        self.save()

    def compile_solution(self):
        """
        Compile the statement tex and save to the statement_pdf field.  No latex error handling atm.
        """
        template_name = 'selfgrade/tex/assignment_solution.tex'
        context = {'assignment': self, 'aux_absolute_path': settings.LATEX_AUX_FILE}
        pdf_bytes = compile_template_to_pdf(template_name, context)
        content_file = ContentFile(pdf_bytes)
        self.solution_pdf.save(
            f"assignment_{self.id}_solution.pdf", content_file
        )
        self.save()



class AssignedProblem(models.Model):
    """
    Associates a problem with an assignment, maintaining order.
    """

    problem = models.ForeignKey(
        Problem,
        on_delete=models.PROTECT,
        help_text="The problem assigned.",
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.PROTECT,
        help_text="The assignment this problem is part of.",
    )
    number = models.PositiveIntegerField(
        help_text="The order of this problem within the assignment.",
    )

    @property
    def name(self):
        return self.problem.name

    @property
    def statement_tex(self):
        return self.problem.statement_tex

    @property
    def solution_tex(self):
        return self.problem.solution_tex

    class Meta:
        """
        Make sure the number of each problem is unique in each assignment,
        and that each problem appears at most once.
        """

        unique_together = (("assignment", "number"), ("assignment", "problem"))

    def __str__(self):
        return f"Problem {self.number} on {self.assignment}: {self.problem.name}"


class Submission(models.Model):
    """
    Represents a student's submission for an assignment.
    """

    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        help_text="The registration this submission is associated with.",
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        help_text="The assignment this is a submission for.",
    )
    initial_submission = models.FileField(
        upload_to="initial_submissions/",
        null=True,
        blank=True,
        help_text="PDF file of the initial submission.",
    )
    graded_submission = models.FileField(
        upload_to="graded_submissions/",
        null=True,
        blank=True,
        help_text="PDF file of the graded submission.",
    )
    reviewed_submission = models.FileField(
        upload_to="reviewed_submissions/",
        null=True,
        blank=True,
        help_text="PDF file of the reviewed submission.",
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time the submission was made.  Null prior to submission.",
    )
    graded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time the submission was graded.  Null prior to grading.",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time the submission was reviewed.  Null prior to review.",
    )

    def __str__(self):
        return f"Submission for {self.assignment} by {self.registration.user}"


class GradedPart(models.Model):
    """
    Stores grading information for a specific part of a submission.
    """

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        help_text="The submission being graded.",
    )
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        help_text="The specific part being graded.",
    )
    self_grade = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="The student's self-assessment grade for this part.",
    )
    grade_guess = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="The student's guess of the grader's grade for this part.",
    )
    guess_confidence = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="The student's confidence in their grade guess (1-5 scale).",
    )
    grade = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="The actual grade given by the grader for this part.",
    )

    def __str__(self):
        return f"Grading for Part {self.part.number} in {self.submission}"
