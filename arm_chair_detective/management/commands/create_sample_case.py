"""
Create a sample case with clues generated from the perpetrator's attributes.
Usage: python manage.py create_sample_case [--perpetrator-id PK] [--case-title "Title"]
"""
from django.core.management.base import BaseCommand
from arm_chair_detective.models import Suspect, Case, Clue


def build_clues_for_perpetrator(perpetrator):
    """Generate realistic clue content and filter_hints from perpetrator attributes."""
    clues_data = []
    
    # Eyewitness account - describes physical appearance
    physical_desc = []
    if perpetrator.hair_color != 'unknown':
        physical_desc.append(f"{perpetrator.get_hair_color_display()} hair")
    if perpetrator.eye_color != 'unknown':
        physical_desc.append(f"{perpetrator.get_eye_color_display()} eyes")
    if perpetrator.build != 'unknown':
        physical_desc.append(f"{perpetrator.get_build_display()} build")
    if perpetrator.height_range != 'unknown':
        physical_desc.append(f"{perpetrator.get_height_range_display()}")
    
    age_phrase = ""
    if perpetrator.age_range != 'unknown':
        age_word = perpetrator.get_age_range_display().split()[0]  # e.g. "Teenager" or "20s"
        age_phrase = f" Looked like they were in their {age_word.lower()}."
    eyewitness_content = (
        f"Witness stated: 'I saw someone running from the scene. "
        f"They had {', '.join(physical_desc) if physical_desc else 'no clear distinguishing features'}.{age_phrase} "
        f"Couldn't tell the vehicle color from where I was.'"
    )
    clues_data.append({
        'clue_type': 'eyewitness',
        'title': 'Witness Account - Main Street',
        'content': eyewitness_content,
        'order': 1,
        'filter_hints': {
            'hair_color': perpetrator.hair_color,
            'eye_color': perpetrator.eye_color,
            'build': perpetrator.build,
            'height_range': perpetrator.height_range,
            'age_range': perpetrator.age_range,
        },
    })

    # 911 call transcript - may include accent, gender, vehicle
    call_content = (
        f"[911 DISPATCH RECORDING - Transcript]\n"
        f"Caller: 'Someone just broke into the building! I saw a {perpetrator.get_gender_display().lower()} "
        f"get into a {perpetrator.get_vehicle_color_display()} {perpetrator.get_vehicle_type_display()} "
        f"and drive off toward the highway!'\n"
        f"Operator: 'Can you describe the person?'\n"
        f"Caller: 'They had {perpetrator.get_hair_color_display()} hair, I think. "
        f"Sounded like they might have a {perpetrator.get_accent_region_display().lower()} accent when they yelled something.'"
    )
    clues_data.append({
        'clue_type': '911_call',
        'title': '911 Call Transcript',
        'content': call_content,
        'order': 2,
        'filter_hints': {
            'gender': perpetrator.gender,
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
            'hair_color': perpetrator.hair_color,
            'accent_region': perpetrator.accent_region,
        },
    })

    # Video analysis
    video_content = (
        f"[SURVEILLANCE FOOTAGE ANALYSIS - Case File]\n"
        f"Camera: Parking lot entrance, north side.\n"
        f"Subject observed: {perpetrator.get_gender_display()}, "
        f"{perpetrator.get_build_display()} build, "
        f"{perpetrator.get_height_range_display()}. "
        f"Vehicle: {perpetrator.get_vehicle_color_display()} {perpetrator.get_vehicle_type_display()}. "
        f"Skin tone described as {perpetrator.get_skin_tone_display().lower()} by analysis team."
    )
    clues_data.append({
        'clue_type': 'video_analysis',
        'title': 'Security Footage Analysis',
        'content': video_content,
        'order': 3,
        'filter_hints': {
            'gender': perpetrator.gender,
            'build': perpetrator.build,
            'height_range': perpetrator.height_range,
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
            'skin_tone': perpetrator.skin_tone,
        },
    })

    return clues_data


class Command(BaseCommand):
    help = 'Create a sample case with auto-generated clues from perpetrator attributes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--perpetrator-id',
            type=int,
            help='PK of suspect to use as perpetrator. Random if omitted.',
        )
        parser.add_argument(
            '--case-title',
            type=str,
            default='The Metro Heist',
            help='Title for the new case',
        )
        parser.add_argument(
            '--difficulty',
            type=str,
            choices=['easy', 'medium', 'hard'],
            default='medium',
        )

    def handle(self, *args, **options):
        if options.get('perpetrator_id'):
            perpetrator = Suspect.objects.filter(pk=options['perpetrator_id']).first()
            if not perpetrator:
                self.stdout.write(self.style.ERROR(f'Suspect PK {options["perpetrator_id"]} not found.'))
                return
        else:
            perpetrator = Suspect.objects.order_by('?').first()
            if not perpetrator:
                self.stdout.write(self.style.ERROR(
                    'No suspects in database. Run: python manage.py generate_suspects --count 10000'
                ))
                return

        case = Case.objects.create(
            title=options['case_title'],
            description='A burglary at the downtown metro station. Security was bypassed and valuables were taken. Multiple witnesses and surveillance footage available.',
            perpetrator=perpetrator,
            difficulty=options['difficulty'],
        )

        for data in build_clues_for_perpetrator(perpetrator):
            Clue.objects.create(case=case, **data)

        self.stdout.write(self.style.SUCCESS(
            f'Created case "{case.title}" (PK={case.pk}) with perpetrator {perpetrator.full_name} (PK={perpetrator.pk})'
        ))
        self.stdout.write(f'  Clues: {case.clues.count()}')
