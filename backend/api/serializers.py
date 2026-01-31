from rest_framework import serializers
from .models import EquipmentDataset, EquipmentItem

class EquipmentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentItem
        fields = '__all__'

class EquipmentDatasetSerializer(serializers.ModelSerializer):
    items = EquipmentItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = EquipmentDataset
        fields = '__all__'
