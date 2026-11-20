from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Comparison, Product


class ProductComparisonTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user("buyer", "buyer@example.test")
        cls.other = users.create_user("other", "other@example.test")
        cls.admin = users.create_user("staff", "staff@example.test", is_staff=True)
        cls.first = Product.objects.create(
            owner=cls.owner, name="Atlas", category="Computers", product_type="Laptop",
            price=Decimal("12000.00"), specifications={"RAM": "8 GB"},
        )
        cls.second = Product.objects.create(
            owner=cls.owner, name="Birch", category="Computers", product_type=" laptop ",
            price=Decimal("16000.00"), specifications={"ram": "16 GB", "Storage": "512 GB"},
        )
        cls.third = Product.objects.create(
            owner=cls.owner, name="Camera", category="Electronics", product_type="Camera",
            price=Decimal("1000.00"), specifications={"Resolution": "12 MP"},
        )
        cls.private = Product.objects.create(
            owner=cls.other, name="Other laptop", category="Computers", product_type="Laptop",
            price=Decimal("15000.00"), specifications={"RAM": "16 GB"},
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def url(self, name, pk=None):
        return reverse(f"products:{name}", args=[pk] if pk is not None else [])

    def save_comparison(self):
        response = self.client.post(self.url("comparison_build"), {
            "action": "save", "title": "Laptop shortlist", "products": [self.first.pk, self.second.pk],
        })
        comparison = Comparison.objects.get(owner=self.owner)
        self.assertRedirects(response, self.url("comparison_detail", comparison.pk))
        return comparison

    def test_product_crud_and_validation(self):
        data = {
            "name": " Cedar ", "category": "Computers", "product_type": "Laptop",
            "price": "0.00", "specifications": "RAM 32 GB",
        }
        response = self.client.post(self.url("add"), data)
        self.assertContains(response, "greater than or equal to 0.01")
        self.assertContains(response, "needs a specification name and a value")
        data.update(price="21000.20", specifications="RAM: 32 GB\nStorage: 1 TB", owner=self.other.pk)
        response = self.client.post(self.url("add"), data)
        product = Product.objects.get(name="Cedar")
        self.assertEqual(product.owner, self.owner)
        self.assertEqual(product.price, Decimal("21000.20"))
        self.assertEqual(product.specifications["Storage"], "1 TB")
        self.assertRedirects(response, self.url("detail", product.pk))
        self.assertContains(self.client.get(self.url("list")), "Cedar")
        self.assertNotContains(self.client.get(self.url("list")), self.private.name)
        self.assertContains(self.client.get(self.url("edit", product.pk)), "RAM: 32 GB")
        data["price"] = "19999.99"
        self.assertRedirects(self.client.post(self.url("edit", product.pk), data), self.url("detail", product.pk))
        product.refresh_from_db()
        self.assertEqual(product.price, Decimal("19999.99"))
        self.assertContains(self.client.get(self.url("delete", product.pk)), "Cedar")
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
        self.assertRedirects(self.client.post(self.url("delete", product.pk)), self.url("list"))
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_guest_and_staff_role_gates(self):
        for user, status in [(None, 302), (self.admin, 403)]:
            self.client.logout()
            if user:
                self.client.force_login(user)
            for name in ["list", "add", "comparison_list", "comparison_build"]:
                with self.subTest(user=user, page=name):
                    self.assertEqual(self.client.get(self.url(name)).status_code, status)

    def test_product_urls_are_private(self):
        for name in ["detail", "edit", "delete"]:
            self.assertEqual(self.client.get(self.url(name, self.private.pk)).status_code, 404)
            self.assertEqual(self.client.post(self.url(name, self.private.pk)).status_code, 404)

    def test_preview_aligns_specifications_without_saving(self):
        response = self.client.post(self.url("comparison_build"), {"products": [self.first.pk, self.second.pk]})
        for content in ["Atlas", "Birch", "8 GB", "16 GB", "512 GB", "Save comparison"]:
            self.assertContains(response, content)
        self.assertEqual(response.context["rows"], [("RAM", ["8 GB", "16 GB"]), ("Storage", [None, "512 GB"])])
        self.assertFalse(Comparison.objects.exists())

    def test_invalid_and_foreign_selections_are_rejected_on_preview_and_save(self):
        extra = [
            Product.objects.create(
                owner=self.owner, name=f"Laptop {i}", category="Computers", product_type="Laptop",
                price=Decimal("18000"), specifications={"RAM": "8 GB"},
            )
            for i in range(3)
        ]
        cases = [
            ([self.first.pk, self.first.pk], "Select between 2 and 4 products."),
            ([self.first.pk, self.second.pk, *(product.pk for product in extra)], "Select between 2 and 4 products."),
            ([self.first.pk, self.third.pk], "Choose products of the same type."),
            ([self.first.pk, self.private.pk], "Choose products that are still in your list."),
        ]
        for action in ["preview", "save"]:
            for products, error in cases:
                with self.subTest(action=action, products=products):
                    response = self.client.post(self.url("comparison_build"), {
                        "action": action, "title": "Invalid comparison", "products": products,
                    })
                    self.assertContains(response, error)
        self.assertFalse(Comparison.objects.exists())

    def test_comparison_crud_and_snapshot_survive_product_changes(self):
        comparison = self.save_comparison()
        Product.objects.filter(pk=self.first.pk).update(name="Edited later")
        self.client.post(self.url("delete", self.second.pk))
        response = self.client.get(self.url("comparison_detail", comparison.pk))
        self.assertContains(response, "Atlas")
        self.assertNotContains(response, "Edited later")
        self.assertContains(response, "Birch")
        self.assertEqual(comparison.items.count(), 2)
        self.assertIsNone(comparison.items.get(name="Birch").product_id)
        updated_name = {"title": "Refined shortlist"}
        self.assertRedirects(
            self.client.post(self.url("comparison_rename", comparison.pk), updated_name),
            self.url("comparison_detail", comparison.pk),
        )
        self.assertContains(self.client.get(self.url("comparison_list")), "Refined shortlist")
        self.assertRedirects(
            self.client.post(self.url("comparison_delete", comparison.pk)), self.url("comparison_list")
        )
        self.assertFalse(Comparison.objects.filter(pk=comparison.pk).exists())

    def test_saved_comparison_urls_are_private(self):
        comparison = self.save_comparison()
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.url("comparison_list")), comparison.title)
        for name in ["comparison_detail", "comparison_rename", "comparison_delete"]:
            url = self.url(name, comparison.pk)
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, {"title": "Forged"}).status_code, 404)
