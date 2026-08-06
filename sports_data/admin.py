from django.contrib import admin
from .models import League, MatchStat

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_id', 'is_active')

@admin.register(MatchStat)
class MatchStatAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'away_team', 'match_date', 'league')
    list_filter = ('league',)