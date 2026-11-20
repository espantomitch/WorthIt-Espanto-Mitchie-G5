from django.urls import path

from . import views

app_name = "products"
urlpatterns = [
    path("", views.product_list, name="list"),
    path("add/", views.product_edit, name="add"),
    path("<int:pk>/", views.product_detail, name="detail"),
    path("<int:pk>/edit/", views.product_edit, name="edit"),
    path("<int:pk>/delete/", views.product_delete, name="delete"),
]
