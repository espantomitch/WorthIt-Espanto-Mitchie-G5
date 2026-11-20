from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("products", "0002_comparison_comparisonitem")]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE products_product ENABLE ROW LEVEL SECURITY;"
            "ALTER TABLE products_comparison ENABLE ROW LEVEL SECURITY;"
            "ALTER TABLE products_comparisonitem ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE products_comparisonitem DISABLE ROW LEVEL SECURITY;"
            "ALTER TABLE products_comparison DISABLE ROW LEVEL SECURITY;"
            "ALTER TABLE products_product DISABLE ROW LEVEL SECURITY;",
        ),
    ]
