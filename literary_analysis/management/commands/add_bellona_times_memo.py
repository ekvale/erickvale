"""
Management command to add analytical memo about Bellona Times references.
"""
from django.core.management.base import BaseCommand
from literary_analysis.models import LiteraryWork, CodebookTemplate, Analysis, AnalyticalMemo
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Add analytical memo about Bellona Times references in Dhalgren'

    def handle(self, *args, **options):
        # Get or create a user
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No user found. Please create a user first.'))
            return

        # Get or create Dhalgren work
        work, created = LiteraryWork.objects.get_or_create(
            title="Dhalgren",
            author="Samuel R. Delany",
            defaults={
                'uploaded_by': user,
                'text_length': 0
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created literary work: {work.title}'))

        # Get or create codebook
        codebook, created = CodebookTemplate.objects.get_or_create(
            name="Dhalgren - Complete Analysis",
            defaults={
                'template_type': 'dhalgren',
                'description': 'Pre-built codebook for analyzing Samuel R. Delany\'s Dhalgren.',
                'is_public': True,
                'created_by': user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created codebook: {codebook.name}'))

        # Get or create analysis
        analysis, created = Analysis.objects.get_or_create(
            literary_work=work,
            codebook=codebook,
            analyst=user,
            defaults={}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created analysis: {analysis}'))

        # Create the memo about Bellona Times references
        memo_content = """<h2>References in the Bellona Times: Real-Life Connections and Symbolic Meanings</h2>

<p>The <strong>Bellona Times</strong> newspaper in <em>Dhalgren</em> serves as a crucial intertextual layer, connecting the fictional apocalypse of Bellona to real-world historical and cultural references. Delany uses these references to create multiple layers of meaning that comment on both the novel's internal reality and external social contexts.</p>

<h3>Real-Life Historical References</h3>

<p>The Bellona Times contains numerous references to actual historical events, figures, and cultural movements:</p>

<ul>
<li><strong>Civil Rights Era References:</strong> The newspaper often references events from the 1960s-70s Civil Rights movement, connecting Bellona's social collapse to real historical trauma and resistance movements.</li>

<li><strong>Literary and Cultural Figures:</strong> References to actual writers, artists, and intellectuals appear throughout, creating a metafictional bridge between the fictional world and Delany's own cultural milieu.</li>

<li><strong>Urban Decay and Riots:</strong> The newspaper's coverage of Bellona's destruction mirrors real-world urban crises, particularly referencing events in American cities during the late 1960s and early 1970s.</li>
</ul>

<h3>Symbolic Functions</h3>

<p>The Bellona Times operates symbolically on several levels:</p>

<ol>
<li><strong>Reality Marker:</strong> The newspaper provides a semblance of normalcy and documentation in a world where reality itself is breaking down, creating an ironic contrast between journalistic "objectivity" and Bellona's impossible physics.</li>

<li><strong>Temporal Anchoring:</strong> References to specific dates and events create temporal markers in a narrative where time itself is unstable, serving as both anchors and points of confusion.</li>

<li><strong>Intertextual Network:</strong> The newspaper connects Dhalgren to a web of other texts, historical events, and cultural discourses, expanding the novel's meaning beyond its immediate narrative boundaries.</li>
</ol>

<h3>Contextual Meanings</h3>

<p>Within the context of <em>Dhalgren</em>'s themes:</p>

<ul>
<li>The newspaper represents <strong>failed documentation</strong>—attempts to record and make sense of events that resist conventional understanding</li>

<li>It functions as a <strong>metafictional device</strong>, reminding readers that they are engaging with a constructed text about a constructed reality</li>

<li>The references create <strong>temporal disorientation</strong>, blurring the line between past, present, and the impossible future of Bellona</li>

<li>It serves as a <strong>queer historical archive</strong>, preserving references to marginalized voices and experiences that mainstream history often erases</li>
</ul>

<h3>Key Examples</h3>

<p>Specific references in the Bellona Times that warrant close analysis include:</p>

<ul>
<li>References to actual dates and events that create temporal confusion</li>
<li>Names of real historical figures that appear in impossible contexts</li>
<li>Cultural artifacts (books, films, music) that bridge fictional and real worlds</li>
<li>News items that comment on both Bellona's situation and broader social issues</li>
</ul>

<p><em>This memo should be expanded with specific textual examples from the novel as the analysis progresses.</em></p>
"""

        memo, created = AnalyticalMemo.objects.update_or_create(
            analysis=analysis,
            title="Bellona Times References: Real-Life Connections and Symbolic Meanings",
            defaults={
                'content': memo_content,
                'created_by': user,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created memo: {memo.title}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Updated existing memo: {memo.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'  Analysis ID: {analysis.pk}'))
        self.stdout.write(self.style.SUCCESS(f'  Memo ID: {memo.pk}'))
        self.stdout.write(self.style.SUCCESS(f'\nView at: /apps/literary/analyses/{analysis.pk}/'))

