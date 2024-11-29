from django.db.models import Avg, Max, Min, Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.files.storage import FileSystemStorage
import csv
from django.core.cache import cache
from .models import TestResult
from .serializers import TestResultSerializer



# View to Create a New Test Record
class TestResultCreateView(APIView):
    """
    POST /api/tests/create/ - Create a new test record
    """
    def post(self, request):
        serializer = TestResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View to Get All Tests for a Patient by patient_id
class TestResultListView(APIView):
    """
    GET /api/tests/?patient_id=123 - Get all tests for a patient
    """
    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            tests = TestResult.objects.filter(patient_id=patient_id)
            serializer = TestResultSerializer(tests, many=True)
            return Response(serializer.data)
        return Response({"error": "Patient ID is required."}, status=status.HTTP_400_BAD_REQUEST)


class TestResultStatsView(APIView):
    """
    GET /api/tests/stats/ - Get basic statistics (min, max, avg) for each test type
    """
    def get(self, request):
        # Try to get cached statistics
        print("Attempting to get 'test_stats' from cache...")
        stats = cache.get('test_stats')

        if not stats:
            print("Cache miss: 'test_stats' not found in cache.")
            
            # If not found in cache, calculate stats
            try:
                print("Calculating stats from database...")
                stats = TestResult.objects.values('test_name').annotate(
                    min_value=Min('value'),
                    max_value=Max('value'),
                    avg_value=Avg('value'),
                    total_tests=Count('id'),
                    abnormal_count=Count('id', filter=TestResult.objects.filter(is_abnormal=True))
                )

                # Format the result into a dictionary
                test_stats = {stat['test_name']: {
                    'min_value': stat['min_value'],
                    'max_value': stat['max_value'],
                    'avg_value': stat['avg_value'],
                    'total_tests': stat['total_tests'],
                    'abnormal_count': stat['abnormal_count']
                } for stat in stats}

                print(f"Calculated stats: {test_stats}")

                # Cache the statistics for 5 minutes
                print("Setting 'test_stats' in cache...")
                cache.set('test_stats', test_stats, timeout=300)
                print("Set 'test_stats' in cache.")

            except Exception as e:
                print(f"Error calculating stats: {str(e)}")
                return Response({"error": "Error calculating stats."}, status=500)

        else:
            print(f"Cache hit: 'test_stats' found in cache.")

        return Response({"test_stats": stats})



# View to Batch Upload Test Results via CSV
import logging
import csv
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TestResultSerializer
from .models import TestResult

# Create a logger instance
logger = logging.getLogger(__name__)

class TestResultBatchUploadView(APIView):
    """
    POST /api/tests/batch-upload/ - Batch upload test results via CSV
    """
    def post(self, request):
        # Print the request data for debugging
        print("Request Files:", request.FILES)
        print("Request Data:", request.data)
        
        # Use the correct key to access the file (csv_file instead of file)
        file = request.FILES.get('csv_file')  # Change this key name to 'csv_file'
        
        if not file:
            return Response({"error": "No file uploaded. Please upload a CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the file is a CSV
        if not file.name.endswith('.csv'):
            return Response({"error": "Invalid file format. Please upload a CSV file."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Process the CSV file
        try:
            csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
            errors = []
            for row in csv_reader:
                # Ensure all required fields are present in the CSV
                if not all(key in row for key in ['patient_id', 'test_name', 'value', 'unit', 'test_date', 'is_abnormal']):
                    errors.append(f"Missing fields in row: {row}")
                    continue
                
                data = {
                    'patient_id': row['patient_id'],
                    'test_name': row['test_name'],
                    'value': row['value'],
                    'unit': row['unit'],
                    'test_date': row['test_date'],
                    'is_abnormal': row['is_abnormal']
                }

                serializer = TestResultSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    errors.append(f"Invalid data in row {row}: {serializer.errors}")

            if errors:
                return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
            
            # Optionally clear the cached stats if new records are added
            cache.delete('test_stats')

            return Response({"message": "Batch upload successful."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
