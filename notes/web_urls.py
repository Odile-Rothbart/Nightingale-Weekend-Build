from django.urls import path
from .web_views import patient_page

urlpatterns = [
    path("patients/<int:patient_id>/", patient_page, name="patient_page"),
]
