import json

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import constant_time_compare, salted_hmac

from accounts.decorators import role_required

from .comparison_forms import ComparisonSaveForm, ComparisonSelectionForm, ComparisonTitleForm
from .models import ComparisonItem


def comparison_rows(products):
    labels = {}
    specifications = []
    for product in products:
        values = {}
        for label, value in product.specifications.items():
            key = label.casefold()
            labels.setdefault(key, label)
            values[key] = value
        specifications.append(values)
    return [(labels[key], [values.get(key) for values in specifications]) for key in sorted(labels)]


def preview_signature(owner, products):
    snapshot = [
        [product.pk, product.name, product.category, product.product_type, str(product.price), product.specifications]
        for product in products
    ]
    payload = json.dumps([owner.pk, snapshot], sort_keys=True)
    return salted_hmac("products.comparison-preview", payload, algorithm="sha256").hexdigest()


@role_required(admin=False)
def comparison_list(request):
    return render(request, "products/comparisons.html", {
        "comparisons": request.user.comparisons.all(),
    })


@role_required(admin=False)
@transaction.atomic
def comparison_build(request):
    saving = request.method == "POST" and request.POST.get("action") == "save"
    products = request.user.products.all()
    if saving:
        # Match the lock order used by concurrent saves and hold the records until the snapshots exist.
        products = products.select_for_update().order_by("pk")

    selection = ComparisonSelectionForm(request.POST if request.method == "POST" else None, products=products)
    if request.method != "POST" or not selection.is_valid():
        return render(request, "products/comparison_build.html", {
            "selection": selection,
            "has_products": request.user.products.exists(),
        })

    selected = sorted(selection.cleaned_data["products"], key=lambda product: (product.name, product.pk))
    signature = preview_signature(request.user, selected)
    title_form = ComparisonSaveForm(request.POST if saving else None, initial={"preview_signature": signature})
    if saving and title_form.is_valid() and not constant_time_compare(signature, title_form.cleaned_data["preview_signature"]):
        title_form.add_error("preview_signature", "A product changed since the preview. Choose your products again to review the updated details.")
    if saving and title_form.is_valid():
        comparison, created = request.user.comparisons.get_or_create(
            submission_id=title_form.cleaned_data["submission_key"],
            defaults={"title": title_form.cleaned_data["title"]},
        )
        if created:
            ComparisonItem.objects.bulk_create([
                ComparisonItem(
                    comparison=comparison, product=product, position=position,
                    name=product.name, category=product.category, product_type=product.product_type,
                    price=product.price, specifications=product.specifications,
                )
                for position, product in enumerate(selected, start=1)
            ])
        messages.success(request, "Comparison saved." if created else "This comparison was already saved.")
        return redirect("products:comparison_detail", pk=comparison.pk)

    return render(request, "products/comparison_detail.html", {
        "items": selected, "rows": comparison_rows(selected), "form": title_form,
    })


@role_required(admin=False)
def comparison_detail(request, pk):
    comparison = get_object_or_404(request.user.comparisons.all(), pk=pk)
    items = list(comparison.items.all())
    return render(request, "products/comparison_detail.html", {
        "comparison": comparison, "items": items, "rows": comparison_rows(items),
    })


@role_required(admin=False)
@transaction.atomic
def comparison_rename(request, pk):
    comparisons = request.user.comparisons.all()
    if request.method == "POST":
        comparisons = comparisons.select_for_update()
    comparison = get_object_or_404(comparisons, pk=pk)
    form = ComparisonTitleForm(request.POST if request.method == "POST" else None, instance=comparison)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Comparison renamed.")
        return redirect("products:comparison_detail", pk=comparison.pk)
    return render(request, "products/comparison_manage.html", {"comparison": comparison, "form": form})


@role_required(admin=False)
def comparison_delete(request, pk):
    comparison = get_object_or_404(request.user.comparisons.all(), pk=pk)
    if request.method == "POST":
        comparison.delete()
        messages.success(request, "Comparison deleted.")
        return redirect("products:comparison_list")
    return render(request, "products/comparison_manage.html", {"comparison": comparison})
