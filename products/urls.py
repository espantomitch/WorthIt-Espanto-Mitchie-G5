from django.urls import path

from . import comparison_views, views

app_name = "products"
urlpatterns = [
    path("", views.product_list, name="list"),
    path("add/", views.product_edit, name="add"),
    path("comparisons/", comparison_views.comparison_list, name="comparison_list"),
    path("comparisons/new/", comparison_views.comparison_build, name="comparison_build"),
    path("comparisons/<int:pk>/", comparison_views.comparison_detail, name="comparison_detail"),
    path("comparisons/<int:pk>/rename/", comparison_views.comparison_rename, name="comparison_rename"),
    path("comparisons/<int:pk>/delete/", comparison_views.comparison_delete, name="comparison_delete"),
    path("<int:pk>/", views.product_detail, name="detail"),
    path("<int:pk>/edit/", views.product_edit, name="edit"),
    path("<int:pk>/delete/", views.product_delete, name="delete"),
]
