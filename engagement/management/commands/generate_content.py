from datetime import date, timedelta
from django.core.management.base import BaseCommand
from engagement.models import DailyQuiz, DailyRiddle, DailyTip, WeeklyChallenge
from engagement.ai_service import generate_quiz, generate_riddle, generate_tip, generate_challenge


class Command(BaseCommand):
    help = 'Pre-generate engagement content (quizzes, riddles, tips, challenges)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Number of days to generate (default: 7)')
        parser.add_argument('--today', action='store_true', help='Generate only for today')
        parser.add_argument('--date', type=str, help='Generate for a specific date (YYYY-MM-DD)')
        parser.add_argument('--type', type=str, default='all',
                          choices=['all', 'quiz', 'riddle', 'tip', 'challenge'],
                          help='Type of content to generate')

    def handle(self, *args, **options):
        days = options['days']
        content_type = options['type']

        if options['today']:
            dates = [date.today()]
        elif options['date']:
            try:
                dates = [date.fromisoformat(options['date'])]
            except ValueError:
                self.stderr.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                return
        else:
            dates = [date.today() + timedelta(days=i) for i in range(days)]

        total_generated = 0

        for target_date in dates:
            self.stdout.write(f'Generating content for {target_date}...')

            if content_type in ('all', 'quiz'):
                if not DailyQuiz.objects.filter(quiz_date=target_date).exists():
                    quiz_data, source = generate_quiz()
                    DailyQuiz.objects.create(
                        question=quiz_data['question'],
                        option_a=quiz_data['option_a'],
                        option_b=quiz_data['option_b'],
                        option_c=quiz_data['option_c'],
                        option_d=quiz_data['option_d'],
                        correct_answer=quiz_data['correct_answer'],
                        category=quiz_data.get('category', 'general'),
                        explanation=quiz_data.get('explanation', ''),
                        quiz_date=target_date,
                        generated_by=source,
                    )
                    self.stdout.write(f'  Quiz generated ({source})')
                    total_generated += 1
                else:
                    self.stdout.write(f'  Quiz already exists, skipping')

            if content_type in ('all', 'riddle'):
                if not DailyRiddle.objects.filter(riddle_date=target_date).exists():
                    riddle_data, source = generate_riddle()
                    DailyRiddle.objects.create(
                        question=riddle_data['question'],
                        hint=riddle_data.get('hint', ''),
                        answer=riddle_data['answer'],
                        riddle_date=target_date,
                        generated_by=source,
                    )
                    self.stdout.write(f'  Riddle generated ({source})')
                    total_generated += 1
                else:
                    self.stdout.write(f'  Riddle already exists, skipping')

            if content_type in ('all', 'tip'):
                categories = ['classroom', 'assessment', 'engagement', 'general']
                for cat in categories:
                    if not DailyTip.objects.filter(tip_date=target_date, category=cat).exists():
                        tip_text, source = generate_tip(cat)
                        DailyTip.objects.create(
                            tip=tip_text,
                            category=cat,
                            tip_date=target_date,
                            generated_by=source,
                        )
                        self.stdout.write(f'  Tip generated for {cat} ({source})')
                        total_generated += 1
                    else:
                        self.stdout.write(f'  Tip for {cat} already exists, skipping')

            if content_type in ('all', 'challenge'):
                start = target_date
                end = target_date + timedelta(days=6)
                if not WeeklyChallenge.objects.filter(start_date=start).exists():
                    challenge_data, source = generate_challenge()
                    WeeklyChallenge.objects.create(
                        title=challenge_data['title'],
                        description=challenge_data['description'],
                        challenge_type=challenge_data.get('challenge_type', 'text'),
                        start_date=start,
                        end_date=end,
                        generated_by=source,
                    )
                    self.stdout.write(f'  Challenge generated ({source})')
                    total_generated += 1
                else:
                    self.stdout.write(f'  Challenge already exists for {start}, skipping')

        self.stdout.write(self.style.SUCCESS(f'Done! Generated {total_generated} items.'))
