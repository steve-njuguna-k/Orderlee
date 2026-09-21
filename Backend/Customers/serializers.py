from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    """Serializers registration requests and creates a new Customer."""

    class Meta:
        model = Customer
        fields = "__all__"
