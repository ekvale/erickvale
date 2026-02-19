"""
Create a case inspired by the Nancy Guthrie disappearance (Tucson, Feb 2026).
Uses fictional names. Blends known public facts with plausible invented clues.
Includes: license plate, cell tower, financial, social media, employer records,
statement analysis, audio transcript, timeline pressure.
Perpetrator is 5'9"-5'10" (height_range=medium) and delivery driver (per real case).
Usage: python manage.py create_guthrie_case [--perpetrator-id PK]
"""
from django.core.management.base import BaseCommand
from arm_chair_detective.models import Suspect, Case, Clue


def build_guthrie_clues(perpetrator):
    """Build clues mirroring Nancy Guthrie case + new clue types. Perpetrator must be medium height."""
    clues_data = []

    # CLUE 1: Timeline (0h)
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
        'unlock_after_hours': 0,
        'filter_hints': {},
    })

    # CLUE 2: Doorbell footage (0h) - height fixed at 5'9"-5'10"
    video_content = f"""[FBI - DOORBELL CAMERA ANALYSIS - Recovered from residual cloud data]

Footage recovered despite device tampering. Subject observed:
• Full coverage: mask, gloves, long sleeves, pants, backpack
• Firearm in waistband holster. Analysts note holster placement suggests
  amateur/lack of formal firearms training
• Subject used gloved hand to cover lens, placed potted plants to block view
• Approached archway with head tilted down

FORENSIC ESTIMATES (gait, proportions, frame):
• Estimated build: {perpetrator.get_build_display()}
• Estimated height: 5'9" - 5'10" (average male range, based on doorframe proportions)
• Gender: {perpetrator.get_gender_display()}"""

    clues_data.append({
        'clue_type': 'video_analysis',
        'title': 'Doorbell Camera - Forensic Analysis',
        'content': video_content,
        'order': 2,
        'unlock_after_hours': 0,
        'filter_hints': {
            'build': perpetrator.build,
            'height_range': 'medium',
            'gender': perpetrator.gender,
        },
    })

    # CLUE 3: Neighbor - vehicle (0h)
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
        'unlock_after_hours': 0,
        'filter_hints': {
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
        },
    })

    # CLUE 4: License plate fragment (12h)
    plate_content = f"""[TRAFFIC CAMERA - Oracle Rd & Ina Rd, partial capture]

Vehicle matching witness description ( {perpetrator.get_vehicle_color_display()} {perpetrator.get_vehicle_type_display()} )
passed through intersection at 02:34. Arizona plate, partial read: 4AB-2??
Last digit obscured by glare. Plate format consistent with Tucson-area registration."""

    clues_data.append({
        'clue_type': 'license_plate',
        'title': 'License Plate Fragment - Traffic Camera',
        'content': plate_content,
        'order': 4,
        'unlock_after_hours': 12,
        'filter_hints': {
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
        },
    })

    # CLUE 5: 911 audio transcript (12h) - accent, tone, hesitations
    audio_content = f"""[911 DISPATCH - ANONYMOUS TIP - Audio transcript, 14:22 Sunday]

Operator: "911, what is your emergency?"
Caller: [pause] "I... I might have information. About the Walsh thing."
Operator: "What information do you have?"
Caller: "I saw someone. Last night. Around 2:30. [clears throat] A {perpetrator.get_gender_display().lower()}.
Got into a {perpetrator.get_vehicle_color_display()} {perpetrator.get_vehicle_type_display()}."
Operator: "Can you describe the person?"
Caller: "Uh... {perpetrator.get_hair_color_display()} hair. Looked {perpetrator.get_age_range_display().lower()}.
I couldn't— I didn't get close. [voice drops] Sounded like... {perpetrator.get_accent_region_display().lower()} when they,
uh, muttered something. Maybe to themselves."

[FBI NOTE: Caller exhibited hedging language, hesitation. Reliability: moderate.]"""

    clues_data.append({
        'clue_type': 'audio_transcript',
        'title': '911 Anonymous Tip - Audio Transcript',
        'content': audio_content,
        'order': 5,
        'unlock_after_hours': 12,
        'filter_hints': {
            'gender': perpetrator.gender,
            'hair_color': perpetrator.hair_color,
            'age_range': perpetrator.age_range,
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
            'accent_region': perpetrator.accent_region,
        },
    })

    # CLUE 6: Statement analysis - ransom note (24h)
    ransom_content = f"""[RANSOM NOTE - Excerpt, received by KGUN/KOLD]

"... Wire 6 million USD in Bitcoin to the address below. You have 12 hours.
If we see cops or media stunts, the old lady dies. She's on borrowed time
as it is with that pacemaker. Don't test us..."

[FBI BEHAVIORAL ANALYSIS UNIT - LINGUISTIC ANALYSIS]
• Hedging: Minimal. Writer confident, imperatives ("Wire", "Don't test").
• Regional markers: Tucson/Southwest phrasing; "old lady" common in {perpetrator.get_accent_region_display().lower()} speech.
• Reliability: High. Demands reference victim's medical condition (prior surveillance)."""

    clues_data.append({
        'clue_type': 'statement_analysis',
        'title': 'Ransom Note - Linguistic Analysis',
        'content': ransom_content,
        'order': 6,
        'unlock_after_hours': 24,
        'is_reliable': True,
        'filter_hints': {
            'accent_region': perpetrator.accent_region,
        },
    })

    # CLUE 7: Cell tower pings (24h)
    cell_filter = {'occupation': perpetrator.occupation} if perpetrator.occupation != 'unknown' else {}
    cell_content = """[CELL TOWER DATA - Warrant served, carrier records]

Device linked to ransom communications:
• 23:45 Sat - Tower near Oracle & Ina (Circle K vicinity)
• 01:30 Sun - Tower near Catalina Foothills (Walsh neighborhood)
• 02:35 Sun - Tower near Oracle & Ina (consistent with traffic cam vehicle)
• 03:00 Sun - Tower near Rio Rico corridor (southbound)

Route suggests suspect familiar with Tucson area. Possible delivery/courier work pattern."""

    clues_data.append({
        'clue_type': 'cell_tower',
        'title': 'Cell Tower / Location Data',
        'content': cell_content,
        'order': 7,
        'unlock_after_hours': 24,
        'filter_hints': cell_filter,
    })

    # CLUE 8: Financial records (36h)
    financial_content = f"""[BANK RECORDS - Warrant, person of interest]

• Large cash withdrawal ($2,400) at ATM near Oracle & Ina, Feb 1 @ 10:15 PM
• Recent purchases: prepaid phone (Circle K), gloves (Walmart)
• No significant Bitcoin history prior to incident

[Cross-reference: Withdrawal timing precedes gas station purchase by ~1 hour.
Vehicle observed at ATM matches {perpetrator.get_vehicle_color_display()} {perpetrator.get_vehicle_type_display()}.]
"""

    clues_data.append({
        'clue_type': 'financial',
        'title': 'Financial Records',
        'content': financial_content,
        'order': 8,
        'unlock_after_hours': 36,
        'filter_hints': {
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
        },
    })

    # CLUE 9: Social media (36h)
    social_content = f"""[DIGITAL FOOTPRINT - OSINT]

Accounts linked to ransom wallet / communications:
• References to Tucson, Bitcoin, "easy money"
• Phrasing consistent with {perpetrator.get_accent_region_display().lower()} dialect
• Posts expressing frustration with "respect" and "being overlooked"
• No direct identification; profile scrubbed post-incident"""

    clues_data.append({
        'clue_type': 'social_media',
        'title': 'Social Media / Digital Footprint',
        'content': social_content,
        'order': 9,
        'unlock_after_hours': 36,
        'filter_hints': {
            'accent_region': perpetrator.accent_region,
        },
    })

    # CLUE 10: Employer records (48h) - delivery driver per real case
    occ_filter = {'occupation': perpetrator.occupation} if perpetrator.occupation != 'unknown' else {}
    employer_content = f"""[DMV / EMPLOYMENT RECORDS - Cross-reference]

Persons matching vehicle + physical description + route pattern:
• Employment: {perpetrator.get_occupation_display()}
• DMV lists employer as Tucson-area courier/delivery service
• Route data (cell towers) consistent with delivery driver schedules

[NOTE: Pima County previously detained a delivery driver for questioning; released.
Focus narrowed to individuals with delivery/courier employment and matching attributes.]"""

    clues_data.append({
        'clue_type': 'employer_records',
        'title': 'Employer / Employment Records',
        'content': employer_content,
        'order': 10,
        'unlock_after_hours': 48,
        'filter_hints': occ_filter,
    })

    # CLUE 11: Gas station clerk - full description (48h)
    clerk_content = f"""[WITNESS STATEMENT - Circle K, Oracle & Ina]

Clerk reports a {perpetrator.get_gender_display().lower()} customer,
{perpetrator.get_age_range_display()}, {perpetrator.get_hair_color_display()} hair,
{perpetrator.get_eye_color_display()} eyes, {perpetrator.get_skin_tone_display().lower()} skin,
purchased gloves and a prepaid phone around 11:30 PM. Seemed nervous.
Left in a {perpetrator.get_vehicle_color_display()} {perpetrator.get_vehicle_type_display()}.
Witness identified photo of suspect vehicle make/model from surveillance stills.
Estimated height: 5'9" or so."""

    clues_data.append({
        'clue_type': 'eyewitness',
        'title': 'Gas Station Clerk - Pre-Incident Sighting',
        'content': clerk_content,
        'order': 11,
        'unlock_after_hours': 48,
        'filter_hints': {
            'gender': perpetrator.gender,
            'age_range': perpetrator.age_range,
            'hair_color': perpetrator.hair_color,
            'eye_color': perpetrator.eye_color,
            'skin_tone': perpetrator.skin_tone,
            'vehicle_color': perpetrator.vehicle_color,
            'vehicle_type': perpetrator.vehicle_type,
            'height_range': 'medium',
        },
    })

    return clues_data


class Command(BaseCommand):
    help = 'Create a case inspired by the Nancy Guthrie disappearance (fictionalized)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--perpetrator-id',
            type=int,
            help='PK of suspect to use as perpetrator (must be medium height, delivery_driver).',
        )

    def handle(self, *args, **options):
        if options.get('perpetrator_id'):
            perpetrator = Suspect.objects.filter(pk=options['perpetrator_id']).first()
            if not perpetrator:
                self.stdout.write(self.style.ERROR(f'Suspect PK {options["perpetrator_id"]} not found.'))
                return
            if perpetrator.height_range != 'medium':
                self.stdout.write(self.style.ERROR(
                    f'Guthrie case requires perpetrator 5\'9"-5\'10" (height_range=medium). '
                    f'Suspect {perpetrator.full_name} has {perpetrator.get_height_range_display()}.'
                ))
                return
        else:
            perpetrator = Suspect.objects.filter(
                height_range='medium',
                occupation='delivery_driver',
            ).order_by('?').first()
            if not perpetrator:
                perpetrator = Suspect.objects.filter(height_range='medium').order_by('?').first()
            if not perpetrator:
                self.stdout.write(self.style.ERROR(
                    'No suspects with height 5\'9"-5\'10" (medium) in database. '
                    'Run: python manage.py generate_suspects --count 10000'
                ))
                return

        case = Case.objects.create(
            title='The Catalina Disappearance',
            description='An 84-year-old woman vanishes from her Tucson home in the early hours of February 2nd. Doorbell footage captures a masked intruder. Ransom notes demand millions in Bitcoin. License plates, cell towers, and employer records piece together a timeline of terror.',
            perpetrator=perpetrator,
            difficulty='hard',
        )

        for data in build_guthrie_clues(perpetrator):
            kwargs = {k: v for k, v in data.items() if k != 'is_reliable'}
            kwargs['case'] = case
            clue = Clue.objects.create(**kwargs)
            if data.get('is_reliable') is False:
                clue.is_reliable = False
                clue.save()

        self.stdout.write(self.style.SUCCESS(
            f'Created case "{case.title}" (PK={case.pk}) with perpetrator {perpetrator.full_name} (PK={perpetrator.pk})'
        ))
        self.stdout.write(f'  Height: 5\'9"-5\'10" | Occupation: {perpetrator.get_occupation_display()}')
        self.stdout.write(f'  Clues: {case.clues.count()} (with timeline pressure)')
