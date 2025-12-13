from django.db import models


class Team(models.Model):
    code = models.CharField(max_length=20, unique=True)
    display_name = models.CharField(max_length=120, blank=True)
    mentor_name = models.CharField(max_length=120, blank=True)
    mentor_email = models.EmailField(blank=True)

    def __str__(self):
        return self.display_name or self.code


class Participant(models.Model):
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    language_raw = models.CharField(max_length=50, blank=True)
    academic_level = models.CharField(max_length=10, blank=True)
    competences_raw = models.TextField(blank=True)
    skills_list = models.JSONField(default=list, blank=True)
    language_fr = models.BooleanField(default=False)
    language_en = models.BooleanField(default=False)
    is_dev = models.BooleanField(default=False)
    is_marketing = models.BooleanField(default=False)
    academic_score = models.IntegerField(default=0)
    email_sent = models.BooleanField(default=False)
    is_leader = models.BooleanField(default=False)
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="participants")
    uid = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.full_name or "Participant"
