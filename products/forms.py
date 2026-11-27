from uuid import uuid4

from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    specifications = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "RAM: 16 GB\nStorage: 512 GB"}),
        max_length=4000,
        help_text="Enter one specification per line, using a name followed by a colon and its value.",
    )

    class Meta:
        model = Product
        fields = ["name", "category", "product_type", "price", "specifications"]
        labels = {"price": "Price (PHP)"}
        help_texts = {"product_type": "Use matching types for products you want to compare, such as Laptop."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        specifications = self.initial.get("specifications")
        if isinstance(specifications, dict):
            self.initial["specifications"] = "\n".join(
                f"{label}: {value}" for label, value in sorted(specifications.items())
            )

    def clean_specifications(self):
        specifications = {}
        seen = set()
        for number, line in enumerate(self.cleaned_data["specifications"].splitlines(), start=1):
            if not line.strip():
                continue
            label, colon, value = map(str.strip, line.partition(":"))
            if not colon or not label or not value:
                raise forms.ValidationError(f"Line {number} needs a specification name and a value.")
            if label.casefold() in seen:
                raise forms.ValidationError(f"Enter only one value for {label}.")
            seen.add(label.casefold())
            specifications[label] = value
        return specifications


class ProductCreateForm(ProductForm):
    submission_key = forms.UUIDField(initial=uuid4, widget=forms.HiddenInput, error_messages={
        "required": "Reopen the Add product page before submitting again.",
        "invalid": "Reopen the Add product page before submitting again.",
    })
