from django.db import models
from django.core.files.base import ContentFile
from django_tex.core import compile_template_to_pdf
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
import uuid

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
    num_parts = models.PositiveSmallIntegerField(
        default=1,
        help_text="The number of parts (sub-problems) of the problem"
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
        Compile the statement tex and save to the statement_pdf field.
        Add uuid to filename since it might be in a public media directory.
        (The filename is then not revealed unless the app wants to.)
        No latex error handling atm. I made some changes to the bare package django_tex core.py... careful
        """
        template_name = 'selfgrade/tex/problem_statement.tex'
        context = {'problem': self, 'aux_absolute_path': settings.LATEX_AUX_FILE}
        pdf_bytes = compile_template_to_pdf(template_name, context)
        content_file = ContentFile(pdf_bytes)
        filename = f"problem_{self.id}_statement_{uuid.uuid4()}.pdf"
        self.statement_pdf.save(
            filename, content_file
        )
        self.save()

    def compile_solution(self):
        """
        Compile the solution tex and save to the solution_pdf field.
        Add uuid to filename since it will be in a public media directory.
        (The filename is then not revealed unless the app wants to.)
        No latex error handling atm.
        """
        template_name = 'selfgrade/tex/problem_solution.tex'
        context = {'problem': self, 'aux_absolute_path': settings.LATEX_AUX_FILE}
        pdf_bytes = compile_template_to_pdf(template_name, context)
        content_file = ContentFile(pdf_bytes)
        filename=f"problem_{self.id}_solution_{uuid.uuid4()}.pdf" #obfuscate filename since it will go in a public dir
        self.solution_pdf.save(
            filename, content_file
        )
        self.save()

class Course(models.Model):
    """
    Represents a course with a name and description.
    """

    name = models.CharField(max_length=100, help_text="The name of the course.")
    shortname = models.CharField(max_length=10, help_text="A shorter name")
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

    def get_percentage_grades(self):
        """
        return a dictionary with the percent grade for each assignment for the course
        (keyed by name - make sure names are unique!)
        along with key 'Total' giving the final assignment grade for this course
        """
        assignments = self.course.assignment_set.order_by('due_at')
        submissions = self.submission_set.filter(registration=self)
        percentage_grades = {}
        for assignment in assignments:
            submission = submissions.filter(assignment=assignment).first() #guarnateed unique - returns None if 0
            if submission:
                percentage_grade = submission.get_percentage_grade()
            elif assignment.due_at < timezone.now():
                percentage_grade = 0  # grade is zero if not submitted by deadline
            else:
                percentage_grade = None  # lack of submission is treated as none (drop grade) before deadline
            percentage_grades[assignment.name] = percentage_grade
        numeric_percentage_grades = [float(value) for value in percentage_grades.values() if value is not None]
        numeric_percentage_grades_with_drop = sorted(numeric_percentage_grades)[2:] #drop lowest two
        if numeric_percentage_grades_with_drop:
            percentage_grades['Total'] = sum(numeric_percentage_grades_with_drop) / len(
                numeric_percentage_grades_with_drop)
        else:
            percentage_grades['Total'] = 1

        return percentage_grades


class Assignment(models.Model):
    """
    Represents an assignment given in a course.
    """

    due_at = models.DateTimeField(help_text="The date and time the assignment is due.")
    self_grades_due_at = models.DateTimeField(help_text="The date and time that assignment self-grades are due.")
    #TODO: validate selfgrad due after due
    name = models.CharField(
        max_length=100,
        help_text="The name or title of the assignment.",
    )
    description = models.TextField(
        blank=True,
        help_text="A description of the assignment.",
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
        Compile the statement tex and save to the statement_pdf field.
        Add uuid to filename since it will be in a public media directory.
        (The filename is then not revealed unless the app wants to.)
        No latex error handling atm.
        """
        template_name = 'selfgrade/tex/assignment_statement.tex'
        context = {'assignment': self, 'aux_absolute_path': settings.LATEX_AUX_FILE}
        pdf_bytes = compile_template_to_pdf(template_name, context)
        content_file = ContentFile(pdf_bytes)
        filename = f"assignment_{self.id}_statement.pdf_{uuid.uuid4()}.pdf"
        self.statement_pdf.save(
            filename, content_file
        )
        self.save()

    def compile_solution(self):
        """
        Compile the statement tex and save to the statement_pdf field.
        Add uuid to filename since it will be in a public media directory.
        (The filename is then not revealed unless the app wants to.)
        No latex error handling atm.
        """
        template_name = 'selfgrade/tex/assignment_solution.tex'
        context = {'assignment': self, 'aux_absolute_path': settings.LATEX_AUX_FILE}
        pdf_bytes = compile_template_to_pdf(template_name, context)
        content_file = ContentFile(pdf_bytes)
        filename = f"assignment_{self.id}_solution_{uuid.uuid4()}.pdf"
        self.solution_pdf.save(filename, content_file)
        self.save()

    def is_after_deadline(self):
        return timezone.now() > self.due_at

    def is_after_self_grading_deadline(self):
        return timezone.now() > self.self_grades_due_at




class AssignedProblem(models.Model):
    """
    Associates a problem with an assignment, maintaining order.  Points are given to parts.
    """

    problem = models.ForeignKey(
        Problem,
        on_delete=models.PROTECT,
        help_text="The problem assigned.",
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
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

    # def clean(self):
    #     """
    #     Make sure that we cannot touch assignedProblems if there is already a submission (have not thought about side effects)
    #     This doesn't work because we can't do things like edit submission due date... the clean signal cascades
    #     """
    #     if self.assignment.id and self.assignment.submission_set.exists():
    #         #we need to make sure it has a primary key before asking about its submission set
    #         #if it doesn't have a primary key we are creating the object
    #         raise ValidationError("There is already a submission for this assigned problem.")

    def __str__(self):
        return f"Problem {self.number} on {self.assignment}: {self.problem.name}"


class AssignedPart(models.Model):
    """
    Represents a part of an assigned problem, storing the points that part is worth.
    """
    assigned_problem = models.ForeignKey(
        AssignedProblem,
        on_delete=models.CASCADE,
        help_text="The assigned problem this part is associated with",
    )
    number = models.PositiveIntegerField(
        help_text="The order of this part within the problem.",
    )
    points = models.PositiveIntegerField(
        help_text="The number of points this part is worth.",
        default=4
    )

    class Meta:
        """
        Make sure ordering is valid
        """

        unique_together = ("assigned_problem", "number")

    def __str__(self):
        return f"Part {self.number} assigned for {self.points} points."

    def get_problem_number(self):
        return self.assigned_problem.number

    def get_label(self):
        return f"{self.get_problem_number()}{settings.SUB_PARTS[self.number-1]}"

    #Drops sublabel if its the only part - db call required
    def get_label_smart(self):
        if AssignedPart.objects.exclude(id=self.id).filter(assigned_problem=self.assigned_problem).exists():
            return self.get_label()
        else:
            return f"{self.get_problem_number()}"


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
    reviewed_by = models.ForeignKey(User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The user who reviewed the submission.",
    )
    reviewer_comments = models.TextField(
        blank=True,
        help_text="Comments from the reviewer (TA or grader).",
    )

    class Meta:
        """
        Each student can submit only one submission for each assignment.
        """
        unique_together = ("registration", "assignment")

    def __str__(self):
        return f"Submission for {self.assignment} by {self.registration.user}"

    def get_percentage_grade(self):
        gradedparts = self.gradedpart_set.select_related()
        num_gradedparts = gradedparts.count()
        num_graded = gradedparts.filter(grade__isnull=False).count()
        #Do checks here because this is a grade that will be used
        if num_gradedparts != num_graded:
            return None
        else:
            #qs = gradedparts.aggregate(total=Sum('points'),score=Sum('final')) #can't use this b/c points is a property not a true field
            score = 0
            points = 0
            for gradedpart in gradedparts:
                score += gradedpart.grade
                points += gradedpart.points
            if points:
                return float(score)/float(points)
            else:
                return None


class GradedPart(models.Model):
    """
    Stores grading information for a specific part of a submission.
    """

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        help_text="The submission being graded.",
    )
    assigned_part = models.ForeignKey(
        AssignedPart,
        on_delete=models.CASCADE,
        help_text="The specific part being graded.",
    )
    self_grade = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="The student's self-assessment grade for this part.",
    )
    grade = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="The actual grade given by the grader for this part.",
    )

    def __str__(self):
        return f"Grading for Part {self.assigned_part.number} in {self.submission}"

    def get_label(self):
        return self.assigned_part.get_label()

    #Drops sublabel if its the only part - db call required
    def get_label_smart(self):
        return self.assigned_part.get_label_smart()

    @property
    def points(self):
        return self.assigned_part.points
