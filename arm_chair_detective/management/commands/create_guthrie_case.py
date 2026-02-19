"""
Create a case inspired by the Nancy Guthrie disappearance (Tucson, Feb 2026).
Uses fictional names. Blends known public facts with plausible invented clues
that make the case solvable within the game's filter mechanics.
Usage: python manage.py create_guthrie_case [--perpetrator-id PK]
"""
from django.core.management.base import BaseCommand
from arm_chair_detective.models import Suspect, Case, Clue


def build_guthrie_clues(perpetrator):
    """Build clues that mirror the Nancy Guthrie case + plausible invented details."""
    clues_data = []

    # CLUE 1: Timeline / 911 summary - mirrors real case
    timeline_content = """[PIMA COUNTY SHERIFF'S OFFICE - INCIDENT TIMELINE]

VICTIM: Helen Walsh, 84. Resident of Catalina Foothills, Tucson. Mother of a prominent TV personality. 
Mentally sharp, fragile health (pacemaker, daily medications).

SATURDAY FEB 1:
• 21:45 - Walsh dropped off at residence after family dinner at daughter's home
• 21:50 - Garage door closes (surveillance)
• 01:47 - Doorbell camera disconnected
• 02:12 - Motion detected near front entrance (recovered from Nest backend)
• 02:28 - Pacemaker monitoring app disconnected from phone

SUNDAY FEB 2:
• 09:00 - Walsh failed to join virtual church (routine)
• 12:03 - 911 call placed by concerned friends
• 12:15 - Deputies arrive. Blood on front porch (confirmed victim's). 
  Front security camera missing. Evidence suggests abduction."""

    clues_data.append({
        'clue_type': 'physical_evidence',
        'title': 'Incident Timeline - Sheriff\'s Office',
        'content': timeline_content,
        'order': 1,
        'filter_hints': {},
    })

    # CLUE 2: Doorbell footage analysis - real case structure + estimated build/height
    video_content = f"""[FBI - DOORBELL CAMERA ANALYSIS - Recovered from residual cloud data]

Footage recovered despite device tampering. Subject observed:
• Full coverage: mask, gloves, long sleeves, pants, backpack
• Firearm in waistband holster. Analysts note holster placement suggests 
  amateur/lack of formal firearms training
• Subject used gloved hand to cover lens, placed potted plants to block view
• Approached archway with head tilted down

FORENSIC ESTIMATES (gait, proportions, frame):
• Estimated build: {perpetrator.get_build_display()}
• Estimated height: 5'9" - 5'10" (average range)
• Gender: {perpetrator.get_gender_display()}"""

    clues_data.append({
        'clue_type': 'video_analysis',
        'title': 'Doorbell Camera - Forensic Analysis',
        'content': video_content,
        'order': 2,
        'filter_hints': {
            'build': perpetrator.build,
            'height_range': 'medium',  # 5'9"-5'10" falls in medium (5'6"-5'11")
            'gender': perpetrator.gender,
        },
    })

    # CLUE 3: Neighbor witness - vehicle (plausible fictional)
    neighbor_content = f"""[WITNESS STATEMENT - Neighbor, 3400 block]

"I couldn't sleep. Heard a car door around 2:20, 2:30. Looked out the window— 
someone was pulling away from the curb near the Walsh place. It was a 
{perpetrator.get_vehicle_color_display()} {perpetrator.get_vehicle_type_display()}. 
Couldn't get the plate. I thought it was weird for that hour but didn't call it in 
until I heard the news the next day." """

    clues_data.append({
        'clue_type': 'eyewitness',
        'title': 'Neighbor Statement - Vehicle Sighting',
        'content': neighbor_content,
        'order': 3,
        'filter_hints': {
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
        },
    })

    # CLUE 4: Ransom note + statement analysis (accent/language)
    ransom_content = f"""[RANSOM NOTE - Excerpt, received by KGUN/KOLD]

"... Wire 6 million USD in Bitcoin to the address below. You have 12 hours. 
If we see cops or media stunts, the old lady dies. She's on borrowed time 
as it is with that pacemaker. Don't test us..."

[FBI BEHAVIORAL ANALYSIS UNIT - NOTE]
Linguistic patterns suggest writer is familiar with Tucson/Southwest. 
Communications analysis indicates {perpetrator.get_accent_region_display().lower()} 
speech patterns. Demands reference victim's medical condition (suggests prior 
surveillance or inside knowledge)."""

    clues_data.append({
        'clue_type': '911_call',
        'title': 'Ransom Note - Statement Analysis',
        'content': ransom_content,
        'order': 4,
        'filter_hints': {
            'accent_region': perpetrator.accent_region,
        },
    })

    # CLUE 5: Gas station clerk - saw someone before incident (plausible)
    clerk_content = f"""[WITNESS STATEMENT - Circle K, Oracle & Ina]

Clerk reports a {perpetrator.get_gender_display().lower()} customer, 
{perpetrator.get_age_range_display()}, {perpetrator.get_hair_color_display()} hair, 
{perpetrator.get_eye_color_display()} eyes, {perpetrator.get_skin_tone_display().lower()} skin, 
purchased gloves and a prepaid phone around 11:30 PM. Seemed nervous. 
Left in a {perpetrator.get_vehicle_color_display()} {perpetrator.get_vehicle_type_display()}. 
Witness identified photo of suspect vehicle make/model from surveillance stills."""

    clues_data.append({
        'clue_type': 'eyewitness',
        'title': 'Gas Station Clerk - Pre-Incident Sighting',
        'content': clerk_content,
        'order': 5,
        'filter_hints': {
            'gender': perpetrator.gender,
            'age_range': perpetrator.age_range,
            'hair_color': perpetrator.hair_color,
            'eye_color': perpetrator.eye_color,
            'skin_tone': perpetrator.skin_tone,
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
        },
    })

    return clues_data


class Command(BaseCommand):
    help = 'Create a case inspired by the Nancy Guthrie disappearance (fictionalized)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--perpetrator-id',
            type=int,
            help='PK of suspect to use as perpetrator. Random if omitted.',
        )

    def handle(self, *args, **options):
        if options.get('perpetrator_id'):
            perpetrator = Suspect.objects.filter(pk=options['perpetrator_id']).first()
            if not perpetrator:
                self.stdout.write(self.style.ERROR(f'Suspect PK {options["perpetrator_id"]} not found.'))
                return
        else:
            # Perpetrator must be 5'9"-5'10" (height_range medium = 5'6"-5'11")
            perpetrator = Suspect.objects.filter(height_range='medium').order_by('?').first()
            if not perpetrator:
                perpetrator = Suspect.objects.order_by('?').first()
            if not perpetrator:
                self.stdout.write(self.style.ERROR(
                    'No suspects in database. Run: python manage.py generate_suspects --count 10000'
                ))
                return

        case = Case.objects.create(
            title='The Catalina Disappearance',
            description='An 84-year-old woman vanishes from her Tucson home in the early hours of February 2nd. Doorbell footage captures a masked intruder. Ransom notes demand millions in Bitcoin. Investigators are piecing together a timeline of terror.',
            perpetrator=perpetrator,
            difficulty='hard',
        )

        for data in build_guthrie_clues(perpetrator):
            Clue.objects.create(case=case, **data)

        self.stdout.write(self.style.SUCCESS(
            f'Created case "{case.title}" (PK={case.pk}) with perpetrator {perpetrator.full_name} (PK={perpetrator.pk})'
        ))
        self.stdout.write(f'  Clues: {case.clues.count()}')
