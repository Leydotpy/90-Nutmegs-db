import datetime
import uuid
from typing import List, AnyStr

from django.db import models
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from apps.match import helpers
from apps.fields import AutoSlugField


class InjuryType(models.Model):
    name = models.CharField(max_length=120)
    code = AutoSlugField(populate_from=("name",))

    objects = models.Manager()

    def __str__(self):
        return str(self.name)


class Injury(models.Model):
    start_date = models.DateField()
    return_date = models.DateField()
    injury = models.ForeignKey(InjuryType, on_delete=models.CASCADE)

    objects = models.Manager()

    class Meta:
        verbose_name = _("Injury")
        verbose_name_plural = _("Injuries")

    def __str__(self):
        return str(self.pk)


class Fitness(models.Model):
    player = models.OneToOneField("Player", on_delete=models.CASCADE)
    injuries = models.ManyToManyField(Injury, blank=True)

    objects = models.Manager()

    @property
    def is_injured(self):
        today = datetime.date.today()
        return bool(self.injuries.filter(start_date__lte=today).filter(return_date__gt=today).exists())

    @property
    def injury_records(self):
        return self.injuries.all()

    def __str__(self):
        return str(self.player)


class Person(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    # team = models.ForeignKey("clubs.Team", on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=120,)
    last_name = models.CharField(max_length=120,)
    middle_name = models.CharField(max_length=120, null=True, blank=True)
    nickname = models.CharField(max_length=120, null=True, blank=True)
    # region = models.ForeignKey("region.Region", on_delete=models.SET_NULL, null=True)
    nations = models.ManyToManyField("region.Country", blank=True)
    # name = models.CharField(max_length=120)
    age = models.PositiveIntegerField(default=0)
    slug = AutoSlugField(populate_from=("id", "name", "code"))
    code = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    retired = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self):
        return str(self.fullname)

    @property
    def fullname(self):
        return self.name

    @property
    def name(self):
        name = self.first_name
        if self.middle_name:
            name += f" {self.middle_name}, "
        name += self.last_name
        return name

    class Meta:
        abstract = True


class Player(Person):
    teams = models.ManyToManyField("clubs.Team", through="PlayerTransfer", through_fields=("player", "team"), blank=True)

    @property
    def injury_records(self):
        return self.fitness.injury_records

    @property
    def is_injured(self):
        return self.fitness.is_injured

    @property
    def goals(self):
        return self.goals.all()

    def get_positions_played(self):
        return self.positions_played.all()

    def filter_positions_played_by(self, position: AnyStr | List[AnyStr]):
        if isinstance(position, list):
            return (
                self.get_positions_played().
                filter(position__position__in=position)
            )
        return self.get_positions_played().filter(
            position__position=position
        )

    def get_goals_experimental_by_position(self, position):
        return helpers.get_player_goals_by_position(self, position)

    def get_current_team(self):
        qs = self.transfers.select_related("team").first()
        return qs.team

    @property
    def goals_experimental(self):
        return helpers.get_goals_by_player(self)

    @property
    def assists(self):
        return self.assists.all()

    def get_transfers(self):
        qs = self.transfers.prefetch_related(Prefetch("contract")).all()
        return qs


class Staff(Person):
    class Job(models.TextChoices):
        HEAD_COACH = "head_coach", _("Head Coach / Manager")
        ASSISTANT_HEAD_COACH = "assistant_head_coach", _("Assistant Head Coach / Manager")
        PHYSIO = "physio", _("Physio Therapist")
        DOCTOR = "doctor", _("Club Doctor")
        COACH = "coach", _("Coach")

    job = models.CharField(max_length=50, choices=Job.choices, default=Job.HEAD_COACH)
    teams = models.ManyToManyField("clubs.Team", through="StaffTransfer", through_fields=("staff", "team"), blank=True)

    class Meta(Person.Meta):
        verbose_name = _("Backroom Staff")
        verbose_name_plural = _("Backroom Staffs")


class Contract(models.Model):
    #player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="contracts")
    salary = models.PositiveIntegerField(default=0)
    per_week = models.PositiveIntegerField(default=0)
    per_month = models.PositiveIntegerField(default=0)
    per_year = models.PositiveIntegerField(default=0)
    after_tax = models.PositiveIntegerField(default=0)
    before_tax = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    terminated = models.BooleanField(default=False)
    minimum_release_fee = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.salary)


class PlayerTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True, editable=False)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="transfers")
    team = models.ForeignKey("clubs.Team", on_delete=models.SET_NULL, null=True, related_name="transfers")
    fee = models.PositiveIntegerField(default=0)
    date = models.DateField()
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, related_name="transfers")
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.player)

    class Meta:
        ordering = ["-timestamp"]


class StaffTransfer(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    team = models.ForeignKey("clubs.Team", on_delete=models.SET_NULL, null=True)
    fee = models.PositiveIntegerField(default=0)
    date = models.DateField()
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.staff)