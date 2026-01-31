import pandas as pd
from django.http import HttpResponse
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import EquipmentDataset, EquipmentItem
from .serializers import EquipmentDatasetSerializer, EquipmentItemSerializer
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class UploadCSVView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        try:
            df = pd.read_csv(file)
            
            # Basic validation
            required_columns = ['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature']
            if not all(col in df.columns for col in required_columns):
                return Response({"error": f"Invalid CSV. Required headers: {required_columns}"}, status=status.HTTP_400_BAD_REQUEST)
            
            if df.empty:
                return Response({"error": "The uploaded CSV file is empty."}, status=status.HTTP_400_BAD_REQUEST)

            # Create dataset record
            dataset = EquipmentDataset.objects.create(
                file_name=file.name,
                total_count=len(df),
                avg_flowrate=float(df['Flowrate'].mean()),
                avg_pressure=float(df['Pressure'].mean()),
                avg_temperature=float(df['Temperature'].mean())
            )
            
            # Save items
            items = []
            for _, row in df.iterrows():
                items.append(EquipmentItem(
                    dataset=dataset,
                    name=str(row['Equipment Name']),
                    type=str(row['Type']),
                    flowrate=float(row['Flowrate']),
                    pressure=float(row['Pressure']),
                    temperature=float(row['Temperature'])
                ))
            EquipmentItem.objects.bulk_create(items)
            
            # Keep only last 5
            datasets_to_keep = EquipmentDataset.objects.order_by('-uploaded_at')[:5].values_list('id', flat=True)
            EquipmentDataset.objects.exclude(id__in=datasets_to_keep).delete()
            
            return Response(EquipmentDatasetSerializer(dataset).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            traceback.print_exc() # Log to terminal
            return Response({"error": f"Processing error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class DataSummaryView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk=None):
        if pk:
            dataset = EquipmentDataset.objects.filter(pk=pk).first()
        else:
            dataset = EquipmentDataset.objects.order_by('-uploaded_at').first()
            
        if not dataset:
            return Response({"error": "No data available"}, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate type distribution
        items = dataset.items.all()
        if not items.exists():
             return Response({"error": "Dataset has no items"}, status=status.HTTP_404_NOT_FOUND)

        df = pd.DataFrame(list(items.values('type', 'flowrate', 'pressure', 'temperature')))
        type_dist = df['type'].value_counts().to_dict() if 'type' in df.columns else {}
        
        return Response({
            "id": dataset.id,
            "file_name": dataset.file_name,
            "total_count": dataset.total_count,
            "averages": {
                "flowrate": dataset.avg_flowrate,
                "pressure": dataset.avg_pressure,
                "temperature": dataset.avg_temperature
            },
            "type_distribution": type_dist,
            "data": EquipmentItemSerializer(items, many=True).data
        })

class HistoryView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        datasets = EquipmentDataset.objects.order_by('-uploaded_at')[:5]
        serializer = EquipmentDatasetSerializer(datasets, many=True)
        return Response(serializer.data)

class GeneratePDFView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        dataset = EquipmentDataset.objects.filter(pk=pk).first()
        if not dataset:
            return HttpResponse("Dataset not found", status=404)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_{dataset.id}.pdf"'
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, f"Equipment Parameter Report: {dataset.file_name}")
        p.drawString(100, 730, f"Date: {dataset.uploaded_at}")
        p.drawString(100, 710, f"Total Equipment: {dataset.total_count}")
        p.drawString(100, 690, f"Avg Flowrate: {dataset.avg_flowrate:.2f}")
        p.drawString(100, 670, f"Avg Pressure: {dataset.avg_pressure:.2f}")
        p.drawString(100, 650, f"Avg Temperature: {dataset.avg_temperature:.2f}")
        
        # List some items
        y = 600
        p.drawString(100, y, "Equipment Details (First 10):")
        y -= 20
        items = dataset.items.all()[:10]
        for item in items:
            p.drawString(100, y, f"{item.name} - {item.type}: {item.flowrate} F, {item.pressure} P, {item.temperature} T")
            y -= 15
            if y < 100:
                p.showPage()
                y = 750
        
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
