from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction

from finance.models import (
    OpeningBalance, OpeningBalanceHistory, PeriodClose, Reconciliation
)
from finance.serializers import (
    OpeningBalanceSerializer, OpeningBalanceHistorySerializer,
    PeriodCloseSerializer, ReconciliationSerializer
)
from accounts.permissions import require_permission
from .base import _param

class OpeningBalanceViewSet(viewsets.ModelViewSet):
    queryset = OpeningBalance.objects.select_related('account').all()
    serializer_class = OpeningBalanceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        fiscal_year = _param(self.request, 'fiscal_year', 'fiscalYear')
        if fiscal_year:
            qs = qs.filter(fiscal_year=int(fiscal_year))
        account = _param(self.request, 'account')
        if account:
            qs = qs.filter(account__name=account)
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'history']:
            return [require_permission('finance:read')()]
        return [require_permission('finance:write')()]

    def perform_update(self, serializer):
        instance = self.get_object()
        old_amount = instance.amount
        with db_transaction.atomic():
            serializer.save(updated_by=str(self.request.user.id))
            OpeningBalanceHistory.objects.create(
                fiscal_year=instance.fiscal_year,
                account=instance.account,
                old_amount=old_amount,
                new_amount=serializer.validated_data.get('amount', old_amount),
                changed_by=str(self.request.user.id),
            )

    @action(detail=False, methods=['get'])
    def history(self, request):
        qs = OpeningBalanceHistory.objects.select_related('account').all()
        fiscal_year = _param(request, 'fiscal_year', 'fiscalYear')
        account = _param(request, 'account')
        if fiscal_year is not None:
            try:
                qs = qs.filter(fiscal_year=int(fiscal_year))
            except ValueError:
                pass
        if account:
            qs = qs.filter(account__name=account)
        serializer = OpeningBalanceHistorySerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='revert/(?P<history_pk>[^/.]+)')
    def revert(self, request, history_pk=None):
        from rest_framework.exceptions import NotFound
        try:
            history = OpeningBalanceHistory.objects.select_related('account').get(pk=history_pk)
        except OpeningBalanceHistory.DoesNotExist:
            raise NotFound("Opening balance history record not found.")
        with db_transaction.atomic():
            balance, _ = OpeningBalance.objects.select_related('account').get_or_create(
                fiscal_year=history.fiscal_year,
                account=history.account,
            )
            balance.amount = history.old_amount
            balance.updated_by = str(request.user.id)
            balance.save()
        return Response(OpeningBalanceSerializer(balance).data)


class PeriodCloseViewSet(viewsets.ModelViewSet):
    queryset = PeriodClose.objects.all()
    serializer_class = PeriodCloseSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('finance:read')()]
        return [require_permission('finance:admin')()]

    def perform_create(self, serializer):
        serializer.save(closed_by=str(self.request.user.id))

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReconciliationViewSet(viewsets.ModelViewSet):
    queryset = Reconciliation.objects.select_related('account').all()
    serializer_class = ReconciliationSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('finance:read')()]
        return [require_permission('finance:admin')()]
