from rest_framework import serializers

from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    """Serializers registration requests and creates a new Item."""

    class Meta:
        model = Item
        fields = "__all__"
