from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.http import HttpResponse
from .models import TestResult
import csv
from io import TextIOWrapper


class TestResultAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'test_name', 'value', 'unit', 'test_date', 'is_abnormal']
    change_list_template = "admin/testresult_changelist.html"
    actions = ['export_to_csv']

    def get_urls(self):
        """
        Add a custom URL for CSV upload in the admin.
        """
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.upload_csv, name='testresult_upload_csv'),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        """
        Handle CSV upload and process data with duplicate checking.
        """
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")

            if not csv_file:
                self.message_user(request, "No file uploaded. Please upload a CSV file.", level=messages.ERROR)
                return redirect("..")  # Redirect back to the admin page

            if not csv_file.name.endswith('.csv'):
                self.message_user(request, "Invalid file format. Please upload a CSV file.", level=messages.ERROR)
                return redirect("..")

            try:
                csv_reader = csv.DictReader(TextIOWrapper(csv_file, encoding='utf-8'))
                success_count = 0
                error_details = []
                duplicate_count = 0

                for row_number, row in enumerate(csv_reader, start=1):
                    try:
                        # Check for required fields
                        required_fields = ['patient_id', 'test_name', 'value', 'unit', 'test_date', 'is_abnormal']
                        if not all(field in row for field in required_fields):
                            error_details.append(f"Row {row_number}: Missing required fields.")
                            continue

                        # Check for duplicate patient_id
                        if TestResult.objects.filter(patient_id=row['patient_id'], test_name=row['test_name']).exists():
                            duplicate_count += 1
                            error_details.append(f"Row {row_number}: Duplicate patient_id '{row['patient_id']}' for test '{row['test_name']}'.")
                            continue

                        # Validate and save each row
                        test_result = TestResult(
                            patient_id=row['patient_id'],
                            test_name=row['test_name'],
                            value=row['value'],
                            unit=row['unit'],
                            test_date=row['test_date'],
                            is_abnormal=row['is_abnormal'] == 'True'
                        )
                        test_result.save()
                        success_count += 1

                    except Exception as e:
                        error_details.append(
                            f"Row {row_number}: {row} - Error: {str(e)}"
                        )

                # Feedback to user
                if success_count > 0:
                    self.message_user(request, f"{success_count} rows successfully uploaded.", level=messages.SUCCESS)

                if duplicate_count > 0:
                    self.message_user(request, f"{duplicate_count} duplicate rows were skipped.", level=messages.WARNING)

                if error_details:
                    # Limit the number of errors displayed in the message
                    error_summary = "\n".join(error_details[:5])  # Display the first 5 errors
                    remaining_errors = len(error_details) - 5
                    if remaining_errors > 0:
                        error_summary += f"\n... and {remaining_errors} more errors."

                    self.message_user(
                        request,
                        f"Some rows could not be uploaded:\n{error_summary}",
                        level=messages.ERROR
                    )

                return redirect("..")

            except Exception as e:
                self.message_user(request, f"Error reading CSV file: {str(e)}", level=messages.ERROR)
                return redirect("..")

        return redirect("..")

    def export_to_csv(self, request, queryset):
        """
        Export the selected TestResult records to a CSV file.
        """
        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="test_results.csv"'

        writer = csv.writer(response)
        writer.writerow(['Patient ID', 'Test Name', 'Value', 'Unit', 'Test Date', 'Is Abnormal'])

        # Write the data for each selected TestResult
        for test_result in queryset:
            writer.writerow([test_result.patient_id, test_result.test_name, test_result.value,
                             test_result.unit, test_result.test_date, test_result.is_abnormal])

        return response

    export_to_csv.short_description = "Export Selected to CSV"


admin.site.register(TestResult, TestResultAdmin)
