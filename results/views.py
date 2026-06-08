from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from .models import Result
from students.models import Student
from .serializers import ResultSerializer
from accounts.permissions import require_permission


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.select_related('student').all()
    serializer_class = ResultSerializer
    filterset_fields = ['student_id', 'session', 'term']

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        student_id = self.kwargs.get('student_id')
        if student_id and 'student' not in data:
            data['student'] = student_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('results:read')()]
        if self.action in ['destroy', 'delete_class_results']:
            return [require_permission('results:admin')()]
        return [require_permission('results:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.kwargs.get('student_id')
        if student_id:
            qs = qs.filter(student_id=student_id)
        class_id = self.request.query_params.get('class_id')
        if class_id:
            qs = qs.filter(student__school_class_id=class_id)
        return qs

    @action(detail=False, methods=['get'])
    def class_results(self, request, class_id=None):
        if not class_id:
            class_id = request.query_params.get('class_id')
        session = request.query_params.get('session')
        term = request.query_params.get('term')
        


        if not all([class_id, session]):
            return Response({'error': 'class_id and session required'}, status=400)

        filters = {
            'student__school_class_id': class_id,
            'session': session,
        }
        if term:
            filters['term'] = term

        qs = self.get_queryset().filter(**filters).select_related('student')

        limit = int(request.query_params.get('limit', 200) if str(request.query_params.get('limit', '200')).isdigit() else 200)
        serializer = self.get_serializer(qs[:limit], many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'])
    def delete_class_results(self, request, class_id=None):
        if not class_id:
            class_id = request.query_params.get('class_id')
        session = request.query_params.get('session')
        term = request.query_params.get('term')

        if not all([class_id, session, term]):
            return Response({'error': 'class_id, session, term required'}, status=400)

        with db_transaction.atomic():
            deleted, _ = Result.objects.filter(
                student__school_class_id=class_id,
                session=session,
                term=term,
            ).delete()
        return Response({'deleted': deleted})
