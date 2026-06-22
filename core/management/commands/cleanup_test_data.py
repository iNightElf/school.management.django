from django.core.management.base import BaseCommand
from django.db import transaction
import re

from accounts.models import User
from core.models import SchoolClass, Subject, AcademicYear, Category, SchoolSetting
from students.models import Student
from teachers.models import Teacher
from staff.models import Staff
from books.models import Book
from results.models import Result
from finance.models import (
    Transaction, FeeSchedule, FeeWaiver, StudentFeeAssignment,
    PaymentAllocation, OpeningBalance, OpeningBalanceHistory,
    PeriodClose, Reconciliation, AccountBalance,
)


def _is_test_year(name):
    """Matches AcademicYear names with random hex suffixes like '2026-a7f0f52f'"""
    return bool(re.match(r'^\d{4}-[a-f0-9]{5,}$', name))


class Command(BaseCommand):
    help = 'Remove test artifacts (dry-run with --dry-run). Targets: Result duplicates, AcademicYear hex-suffix entries, test Transactions, test users.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted')
        parser.add_argument('--force', action='store_true', help='Actually execute deletions (omit for safe preview)')
        parser.add_argument('--all-results', action='store_true', help='Delete ALL Result records (not just test ones)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if not dry_run and not force:
            self.stdout.write(self.style.WARNING(
                'This is a destructive command. Use --dry-run to preview, then --force to execute.'
            ))
            return
        records = {}

        # ── AcademicYear: ones with random hex suffixes ──
        ac_years = AcademicYear.objects.all()
        test_academic_years = [y for y in ac_years if _is_test_year(y.name)]
        test_academic_year_ids = [y.id for y in test_academic_years]
        records['AcademicYear (hex-suffix)'] = len(test_academic_years)

        # Delete dependent finance records for these years
        fs_in_test_years = FeeSchedule.objects.filter(academic_year_id__in=test_academic_year_ids)
        test_fs_ids = list(fs_in_test_years.values_list('id', flat=True))
        records['FeeSchedule (test years)'] = len(test_fs_ids)

        # PaymentAllocations & waivers & assignments for those fee schedules
        pa_test = PaymentAllocation.objects.filter(fee_schedule_id__in=test_fs_ids)
        records['PaymentAllocation (test years)'] = pa_test.count()

        fw_test = FeeWaiver.objects.filter(fee_schedule_id__in=test_fs_ids)
        records['FeeWaiver (test years)'] = fw_test.count()

        sfa_test = StudentFeeAssignment.objects.filter(fee_schedule_id__in=test_fs_ids)
        records['StudentFeeAssignment (test years)'] = sfa_test.count()

        # ── Transaction: test descriptions ──
        tx_test = Transaction.objects.filter(
            description__in=['Test', 'Test payment', 'Fee', 'CamelCase body test',
                             'Expense test', 'Cancelled by test']
        )
        records['Transaction (test descriptions)'] = tx_test.count()

        # PaymentAllocations for test transactions
        pa_tx = PaymentAllocation.objects.filter(transaction__in=tx_test).exclude(fee_schedule_id__in=test_fs_ids)
        records['PaymentAllocation (test txs)'] = pa_tx.count()

        # AccountBalances for test years or test accounts
        ab_test = AccountBalance.objects.filter(fiscal_year__in=[y.id for y in test_academic_years if isinstance(y.id, int)] + [2026])
        records['AccountBalance (test)'] = ab_test.count()

        # ── Result: all (user mentioned duplicate subject entries) ──
        if options['all_results']:
            result_qs = Result.objects.all()
        else:
            result_qs = Result.objects.filter(term='First Term', session='2026')
        records['Result'] = result_qs.count()

        # ── User: test emails ──
        user_qs = User.objects.filter(email__in=['admin@test.com', 'staff@test.com', 'del@test.com'])
        records['User (test emails)'] = user_qs.count()

        # ── Print summary ──
        if dry_run:
            self.stdout.write('--- Dry Run ---')
            has = False
            for label, count in records.items():
                if count:
                    has = True
                    self.stdout.write('  Would delete %d %s' % (count, label))
            if not has:
                self.stdout.write('  No test data found')
            else:
                self.stdout.write('  Would delete %d records total' % sum(records.values()))
            return

        # ── Execute deletions in FK-safe order ──
        with transaction.atomic():
            pa_test.delete()
            pa_tx.delete()
            fw_test.delete()
            sfa_test.delete()
            PaymentAllocation.objects.filter(transaction__in=tx_test).delete()
            fs_in_test_years.delete()
            tx_test.delete()
            ab_test.delete()
            result_qs.delete()
            user_qs.delete()

            # Delete the test AcademicYears last
            test_academic_years_to_delete = AcademicYear.objects.filter(id__in=test_academic_year_ids)
            test_academic_years_to_delete.delete()

        self.stdout.write('--- Cleanup Complete ---')
        for label, count in records.items():
            if count:
                self.stdout.write('  Deleted %d %s' % (count, label))
        self.stdout.write('  Deleted %d records total' % sum(records.values()))
        self.stdout.write(self.style.SUCCESS('\nTest data cleanup complete.'))
