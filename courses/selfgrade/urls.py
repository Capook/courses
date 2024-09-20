from django.urls import path

from . import views

app_name = "selfgrade"
urlpatterns = [
    path("my-courses/", views.my_courses, name="my_courses"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
    path("review/<int:submission_id>/", views.review, name="review"),
    path("next_review/<int:assignment_id>/", views.next_review, name="next_review"),
    path("review_list/<int:course_id>/", views.review_list, name="review_list"),
    path("grade_report/<int:course_id>/", views.grade_report, name="grade_report"),
    path("grading_instructions/", views.grading_instructions, name="grading_instructions"),
    path("assignment_grades_csv/<int:course_id>/", views.assignment_grades_csv, name="assignment_grades_csv"),
]
