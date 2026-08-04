from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer

from apps.models.notifications import WaiterCall


class WaiterCallSerializer(ModelSerializer):
    table_number = ReadOnlyField(source="table.number")
    call_type_display = ReadOnlyField(source="get_call_type_display")

    class Meta:
        model = WaiterCall
        fields = (
            "id",
            "table",
            "table_number",
            "order",
            "call_type",
            "call_type_display",
            "amount",
            "status",
            "created_at",
            "resolved_at",
        )
        read_only_fields = fields