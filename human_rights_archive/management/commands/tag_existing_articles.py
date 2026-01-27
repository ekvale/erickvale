"""Retroactively apply tags to existing articles using Tag.keywords."""
from django.core.management.base import BaseCommand
from human_rights_archive.models import Article
from human_rights_archive.utils import suggest_article_tags


class Command(BaseCommand):
    help = 'Apply tags to all existing articles based on Tag keywords (title/summary/content).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be tagged without saving',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        total = Article.objects.count()
        tagged = 0
        for article in Article.objects.iterator():
            tags = suggest_article_tags(article.title, article.summary, article.content)
            if tags:
                if not dry_run:
                    article.tags.add(*tags)
                tagged += 1
                if dry_run:
                    self.stdout.write(f'  Would tag: {article.title[:50]}… -> {[t.name for t in tags]}')
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Dry run: would tag {tagged} of {total} articles.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Tagged {tagged} of {total} articles.'))
