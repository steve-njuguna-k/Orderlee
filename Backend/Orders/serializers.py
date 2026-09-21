from rest_framework import serializers

from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Serializes registration requests and creates a new Order."""

    item_name = serializers.StringRelatedField(source="item.name", read_only=True)
    customer_first_name = serializers.StringRelatedField(
        source="customer.first_name", read_only=True
    )
    customer_last_name = serializers.StringRelatedField(
        source="customer.last_name", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_first_name",
            "customer_last_name",
            "item",
            "item_name",
            "quantity",
            "total",
        ]
        read_only_fields = ["total"]
