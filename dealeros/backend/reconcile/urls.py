
from django.urls import path
from reconcile.views import disagreement_list

urlpatterns = [
    path(
        "disagreements/",
        disagreement_list,
        name="disagreement-list"
    ),
]
