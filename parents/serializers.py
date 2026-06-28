from rest_framework import serializers


class ParentStudentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    studentId = serializers.CharField()
    name = serializers.CharField()
    roll = serializers.CharField()
    klass = serializers.CharField()
    session = serializers.CharField()
    photoUrl = serializers.URLField(allow_null=True)


class ParentAttendanceDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    weekday = serializers.IntegerField()
    type = serializers.CharField()
    status = serializers.CharField(allow_null=True, default=None)


class ParentAttendanceSerializer(serializers.Serializer):
    student = serializers.DictField()
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    days = ParentAttendanceDaySerializer(many=True)


class ParentFeeScheduleItemSerializer(serializers.Serializer):
    category = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    frequency = serializers.CharField()
    assigned = serializers.BooleanField()


class ParentFeeStatusSerializer(serializers.Serializer):
    totalDue = serializers.DecimalField(max_digits=12, decimal_places=2)
    totalPaid = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    schedules = ParentFeeScheduleItemSerializer(many=True)


class ParentResultSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    session = serializers.CharField()
    term = serializers.CharField()
    marks = serializers.JSONField()
    comment = serializers.CharField(allow_null=True)
    createdAt = serializers.DateTimeField()
