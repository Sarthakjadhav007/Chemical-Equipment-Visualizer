from django.db import models

class EquipmentDataset(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_count = models.IntegerField(null=True)
    avg_flowrate = models.FloatField(null=True)
    avg_pressure = models.FloatField(null=True)
    avg_temperature = models.FloatField(null=True)
    
    def __str__(self):
        return f"{self.file_name} ({self.uploaded_at})"

class EquipmentItem(models.Model):
    dataset = models.ForeignKey(EquipmentDataset, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    flowrate = models.FloatField()
    pressure = models.FloatField()
    temperature = models.FloatField()

    def __str__(self):
        return self.name
