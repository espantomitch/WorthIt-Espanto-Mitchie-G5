from uuid import uuid4

from django import forms

from .models import Comparison


class ProductChoicesField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, product):
        return f"{product.name} · {product.product_type} · ₱{product.price:,.2f}"


class ComparisonSelectionForm(forms.Form):
    action = forms.ChoiceField(
        choices=[("preview", "Preview"), ("save", "Save")], required=False,
        error_messages={"invalid_choice": "Choose Preview or Save comparison."},
    )
    products = ProductChoicesField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        error_messages={
            "required": "Select between 2 and 4 products.",
            "invalid_choice": "Choose products that are still in your list.",
        },
    )

    def __init__(self, *args, products, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["products"].queryset = products

    def clean_products(self):
        products = list(self.cleaned_data["products"])
        if not 2 <= len(products) <= 4:
            raise forms.ValidationError("Select between 2 and 4 products.")
        submitted = self.fields["products"].widget.value_from_datadict(self.data, self.files, self.add_prefix("products"))
        if len(submitted) != len(products):
            raise forms.ValidationError("Choose each product only once.")
        if len({" ".join(product.product_type.split()).casefold() for product in products}) != 1:
            raise forms.ValidationError("Choose products of the same type.")
        return products


class ComparisonTitleForm(forms.ModelForm):
    class Meta:
        model = Comparison
        fields = ["title"]
        labels = {"title": "Comparison name"}


class ComparisonSaveForm(ComparisonTitleForm):
    submission_key = forms.UUIDField(initial=uuid4, widget=forms.HiddenInput, error_messages={
        "required": "Choose your products again to start a fresh preview.",
        "invalid": "Choose your products again to start a fresh preview.",
    })
    preview_signature = forms.CharField(max_length=64, widget=forms.HiddenInput, error_messages={
        "required": "Choose your products again to start a fresh preview.",
    })
