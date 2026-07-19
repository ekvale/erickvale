from django.db import models


class HighScore(models.Model):
    """A finished (or lost) run of Math Bastion submitted from the browser."""

    name = models.CharField(max_length=20)
    score = models.PositiveIntegerField()
    era_reached = models.CharField(max_length=60, blank=True, default='')
    waves_cleared = models.PositiveSmallIntegerField(default=0)
    victory = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', 'created_at']
        indexes = [models.Index(fields=['-score'])]

    def __str__(self):
        return f'{self.name} — {self.score}'
