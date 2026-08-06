from django.db import models

class MatchOdds(models.Model):
    match = models.OneToOneField('MatchStat', on_delete=models.CASCADE, related_name='odds')
    home_odds = models.FloatField()
    away_odds = models.FloatField()
    draw_odds = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)
    notified = models.BooleanField(default=False)

class League(models.Model):
    name = models.CharField(max_length=100)
    api_id = models.IntegerField(unique=True)  # ID лиги в API-Football
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (ID: {self.api_id})"

class MatchStat(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    home_goals = models.IntegerField()
    away_goals = models.IntegerField()
    match_date = models.DateTimeField()

    class Meta:
        ordering = ['-match_date']