from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required

from .forms import ProductCreateForm, ProductForm


@role_required(admin=False)
def product_list(request):
    return render(request, "products/list.html", {"products": request.user.products.all()})


@role_required(admin=False)
def product_detail(request, pk):
    product = get_object_or_404(request.user.products.all(), pk=pk)
    return render(request, "products/detail.html", {
        "product": product,
        "specifications": sorted(product.specifications.items(), key=lambda item: item[0].casefold()),
    })


@role_required(admin=False)
@transaction.atomic
def product_edit(request, pk=None):
    product = None
    if pk is not None:
        products = request.user.products.all()
        if request.method == "POST":
            products = products.select_for_update()
        product = get_object_or_404(products, pk=pk)

    form_class = ProductCreateForm if product is None else ProductForm
    form = form_class(request.POST if request.method == "POST" else None, instance=product)
    if request.method == "POST" and form.is_valid():
        if product is None:
            saved_product, created = request.user.products.get_or_create(
                submission_id=form.cleaned_data["submission_key"],
                defaults={field: form.cleaned_data[field] for field in form.Meta.fields},
            )
            messages.success(request, "Product added." if created else "This product was already added.")
        else:
            saved_product = form.save()
            messages.success(request, "Product updated.")
        return redirect("products:detail", pk=saved_product.pk)

    return render(request, "products/form.html", {"form": form, "product": product})


@role_required(admin=False)
@transaction.atomic
def product_delete(request, pk):
    products = request.user.products.all()
    if request.method == "POST":
        products = products.select_for_update()
    product = get_object_or_404(products, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("products:list")
    return render(request, "products/delete.html", {"product": product})
