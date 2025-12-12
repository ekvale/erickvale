"""
Management command to bulk code segments based on patterns, keywords, or existing data.
Helps increase code coverage by automatically coding segments that match certain criteria.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from literary_analysis.models import Analysis, CodedSegment, Code, LiteraryWork
import re


class Command(BaseCommand):
    help = 'Bulk code segments to increase coverage'

    def add_arguments(self, parser):
        parser.add_argument(
            'analysis_id',
            type=int,
            help='Analysis ID to code',
        )
        parser.add_argument(
            '--min-length',
            type=int,
            default=50,
            help='Minimum segment length in characters (default: 50)',
        )
        parser.add_argument(
            '--max-length',
            type=int,
            default=500,
            help='Maximum segment length in characters (default: 500)',
        )
        parser.add_argument(
            '--overlap',
            action='store_true',
            help='Allow overlapping segments (default: False)',
        )
        parser.add_argument(
            '--code-patterns',
            action='store_true',
            help='Code based on keyword patterns',
        )
        parser.add_argument(
            '--code-dialogue',
            action='store_true',
            help='Code all dialogue segments',
        )
        parser.add_argument
