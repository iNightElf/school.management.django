from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'fee-schedules', views.FeeScheduleViewSet, basename='fee-schedule')
router.register(r'fee-waivers', views.FeeWaiverViewSet, basename='fee-waiver')
router.register(r'student-fee-assignments', views.StudentFeeAssignmentViewSet, basename='student-fee-assignment')
router.register(r'opening-balances', views.OpeningBalanceViewSet, basename='opening-balance')
router.register(r'period-closes', views.PeriodCloseViewSet, basename='period-close')
router.register(r'reconciliations', views.ReconciliationViewSet, basename='reconciliation')
router.register(r'reports', views.ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
    path('balances/', views.TransactionViewSet.as_view({'get': 'balances'}), name='balances'),
    path('ledger/', views.TransactionViewSet.as_view({'get': 'ledger'}), name='ledger'),
    path('dashboard-summary/', views.TransactionViewSet.as_view({'get': 'dashboard_summary'}), name='dashboard-summary'),
    path('fee-status/', views.TransactionViewSet.as_view({'get': 'fee_status'}), name='fee-status'),
    path('defaulter/', views.TransactionViewSet.as_view({'get': 'defaulter'}), name='defaulter'),
]


