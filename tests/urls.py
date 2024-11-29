# urls.py

from django.urls import path
from .views import TestResultCreateView, TestResultListView, TestResultStatsView, TestResultBatchUploadView

urlpatterns = [
    path('api/tests/', TestResultListView.as_view(), name='test-result-list'),  # Handle GET for listing tests
    path('api/tests/create/', TestResultCreateView.as_view(), name='test-result-create'),  # Handle POST for creating tests
    path('api/tests/stats/', TestResultStatsView.as_view(), name='test-result-stats'),
    path('api/tests/batch-upload/', TestResultBatchUploadView.as_view(), name='testresult_batch_upload'),
]
