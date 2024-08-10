from django.urls import path

from . import views

app_name = "selfgrade"
urlpatterns = [
    path("my-courses/", views.my_courses, name="my_courses"),
    path("testpdf/", views.testpdf, name="testpdf"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
]
