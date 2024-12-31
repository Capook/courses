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
    path("assignment_grade_report/<int:course_id>/", views.assignment_grade_report, name="assignment_grade_report"),
    path("grading_instructions/", views.grading_instructions, name="grading_instructions"),
    path("assignment_grades_csv/<int:course_id>/", views.assignment_grades_csv, name="assignment_grades_csv"),
    path("course/<int:course_id>", views.course, name="course"),
    path("grading/<int:course_id>", views.grading, name="grading"),
]

htmx_urlpatterns = [
    path("courses/<int:course_id>/update_name", views.update_course_name, name="update_course_name"),
    path("courses/<int:course_id>/update_description", views.update_course_description,
         name="update_course_description"),
    path("materials/delete/<int:material_id>", views.delete_material, name="delete_material"),
    path("materials/create/", views.create_material, name="create_material"),
    path("materials/update/<int:material_id>", views.update_material, name="update_material"),
    path("reorder_materials/<int:course_id>", views.reorder_materials, name="reorder_materials"), #repath?
    path("assignments/delete/<int:assignment_id>", views.delete_assignment, name="delete_assignment"),
    path("assignments/create/", views.create_assignment, name="create_assignment"),
    path("assignments/update/<int:assignment_id>", views.update_assignment, name="update_assignment"),
    path("assignments/update_parts/<int:assignment_id>", views.update_parts, name="update_parts"),
    path("reorder_assignments/<int:course_id>", views.reorder_assignments, name="reorder_assignments"),#repath?
    path("assignments/submit", views.submit_assignment, name="submit_assignment"),
    path("submit_grading/<int:submission_id>", views.submit_grading, name="submit_grading"),
    path("assignment_grade_table/<int:course_id>",views.assignment_grade_table, name="assignment_grade_table"),
]

urlpatterns += htmx_urlpatterns
