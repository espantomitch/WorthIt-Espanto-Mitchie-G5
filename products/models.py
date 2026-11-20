from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80)
    product_type = models.CharField("product type", max_length=80)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    specifications = models.JSONField()

    class Meta:
        ordering = ["name", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name="product_price_positive")]

    def __str__(self):
        return self.name


class Comparison(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comparisons")
    title = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title


class ComparisonItem(models.Model):
    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE, related_name="items")
    # Keep the captured values even when the source product is deleted.
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="comparison_items")
    position = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80)
    product_type = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    specifications = models.JSONField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["comparison", "position"], name="comparison_unique_position"),
            models.UniqueConstraint(fields=["comparison", "product"], name="comparison_unique_product"),
            models.CheckConstraint(condition=models.Q(position__range=(1, 4)), name="comparison_position_range"),
            models.CheckConstraint(condition=models.Q(price__gt=0), name="comparison_price_positive"),
        ]
