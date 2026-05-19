from django.db import models


class LeaderBriefing(models.Model):
    leader_id = models.SlugField()
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=150)
    bureau = models.CharField(max_length=150)
    date = models.DateField()
    schedule = models.JSONField()
    core_beliefs = models.TextField()
    vision = models.TextField()
    top_priorities = models.JSONField()
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('leader_id', 'date')
        ordering = ['-date', 'leader_id']

    def __str__(self):
        return f'{self.name} — {self.date}'
