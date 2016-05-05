from __future__ import unicode_literals
from django.db import models

from main.models import AbstractSiteVisitObservation, AbstractLookup, SpeciesObservation, DATUM_CHOICES, MODEL_SRID, \
    LocationLookup


class Trap(AbstractSiteVisitObservation):
    trapline_ID = models.CharField(max_length=50, null=True, blank=True,
                                   verbose_name="Trap Line ID", help_text="")
    trap_type = models.ForeignKey('TrapTypeLookup', null=False, blank="", on_delete=models.PROTECT,
                                  verbose_name="Trap Type")
    open_date = models.DateField(null=True, blank=True,
                                 verbose_name="Open Date", help_text="")
    close_date = models.DateField(null=True, blank=True,
                                  verbose_name="Close Date", help_text="")
    datum = models.IntegerField(null=True, blank=True, choices=DATUM_CHOICES, default=MODEL_SRID,
                                verbose_name="Datum", help_text="")
    start_latitude = models.FloatField(null=True, blank=True,
                                       verbose_name="Start Latitude", help_text="")
    start_longitude = models.FloatField(null=True, blank=True,
                                        verbose_name="Start Longitude", help_text="")
    stop_latitude = models.FloatField(null=True, blank=True,
                                      verbose_name="Stop Latitude", help_text="")
    stop_longitude = models.FloatField(null=True, blank=True,
                                       verbose_name="Stop Longitude", help_text="")
    accuracy = models.FloatField(default=30.0, null=False, blank=False,
                                 verbose_name="Accuracy (m)", help_text="")
    traps_number = models.IntegerField(null=True, blank=True,
                                       verbose_name="Number of Traps", help_text="")
    comments = models.TextField(blank=True,
                                verbose_name="Comments", help_text="")

    def __unicode__(self):
        return '{} ({})'.format(self.trapline_ID, self.trap_type.value)


class AnimalObservation(AbstractSiteVisitObservation):
    collector = models.CharField(max_length=300, blank=True,
                                 verbose_name="Collector", help_text="")
    date = models.DateField(null=True, blank=True,
                            verbose_name="Observation Date", help_text="")
    trap_no = models.CharField(max_length=20, blank=True,
                               verbose_name="Trap No", help_text="")
    trap_type = models.ForeignKey('TrapTypeLookup', null=True, blank="", on_delete=models.PROTECT,
                                  verbose_name="Trap Type")
    capture_type = models.ForeignKey('CaptureTypeLookup', null=True, blank=True, on_delete=models.PROTECT,
                                     verbose_name="Capture Type", help_text="")
    species = models.ForeignKey(SpeciesObservation, null=False, blank=False,
                                verbose_name="Species", help_text="")
    sex = models.ForeignKey('SexLookup', null=True, blank=True, on_delete=models.PROTECT,
                            verbose_name="Sex", help_text="")
    microchip_id = models.CharField(max_length=30, blank=True,
                                    verbose_name="Microchip number", help_text="")
    tissue_number = models.CharField(max_length=30, blank=True,
                                     verbose_name="Sample number",
                                     help_text="Enter the sample number (e.g. tag number, DNA sample number)")
    tissue_type = models.CharField(max_length=30, blank=True,
                                   verbose_name="DNA sample type",
                                   help_text="Enter DNA sample type (e.g. earclip, scute clip, hair sample)")
    fate = models.CharField(max_length=100, blank=True,
                            verbose_name="Fate", help_text="What happened to animal after trapping")
    gross_weight = models.FloatField(null=True, blank=True,
                                     verbose_name="Gross weight (g)", help_text="Total weight of animal + bag (gms)")
    bag_weight = models.FloatField(null=True, blank=True,
                                   verbose_name="Bag weight (g)", help_text="Total weight of bag (gms)")
    net_weight = models.FloatField(null=True, blank=True,
                                   verbose_name="Net weight (g)", help_text="")
    age = models.ForeignKey('AgeLookup', null=True, blank=True, on_delete=models.PROTECT,
                            verbose_name="Age", help_text="")
    head_length = models.FloatField(null=True, blank=True,
                                    verbose_name="Head length (mm)", help_text="")
    pes_length = models.FloatField(null=True, blank=True,
                                   verbose_name="Pes length (mm)", help_text="")
    reproductive_condition = models.CharField(max_length=100, blank=True,
                                              verbose_name="Reproductive condition", help_text="")
    pouch = models.CharField(max_length=100, blank=True,
                             verbose_name="Pouch", help_text="")
    test_length = models.FloatField(null=True, blank=True,
                                    verbose_name="Testes length", help_text="")
    test_width = models.FloatField(null=True, blank=True,
                                   verbose_name="Testes width", help_text="")
    svl = models.FloatField(null=True, blank=True,
                            verbose_name="Head-Body", help_text="")
    tail_length = models.FloatField(null=True, blank=True,
                                    verbose_name="Tail length", help_text="")
    tail_condition = models.CharField(max_length=200, blank=True,
                                      verbose_name="Tail condition", help_text="")
    comments = models.TextField(blank=True,
                                verbose_name="Comments", help_text="")


class OpportunisticObservation(models.Model):
    observation_type = models.ForeignKey('ObservationTypeLookup', null=True, blank=True, on_delete=models.PROTECT,
                                         verbose_name="Observation Type", help_text="e.g: Bird")
    location = models.ForeignKey(LocationLookup, null=True, blank=True, on_delete=models.PROTECT,
                                 verbose_name="Location", help_text="")
    date = models.DateField(null=True, blank=True,
                            verbose_name="Date", help_text="")
    observer = models.CharField(max_length=100, blank=True,
                                verbose_name="Observer", help_text="")
    species = models.ForeignKey(SpeciesObservation, null=True, blank=True,
                                verbose_name="Species", help_text="")
    latitude = models.FloatField(null=True, blank=True,
                                 verbose_name="Latitude", help_text="")
    longitude = models.FloatField(null=True, blank=True,
                                  verbose_name="Longitude", help_text="")
    accuracy = models.FloatField(default=30.0, null=True, blank=True,
                                 verbose_name="Accuracy (m)", help_text="")
    datum = models.IntegerField(null=True, blank=True, choices=DATUM_CHOICES, default=MODEL_SRID,
                                verbose_name="Datum", help_text="")
    comments = models.TextField(blank=True,
                                verbose_name="Comments", help_text="")


#########################
# Lookups
#########################


class ObservationTypeLookup(AbstractLookup):
    strict = False
    pass


class CaptureTypeLookup(AbstractLookup):
    strict = False
    pass


class SexLookup(AbstractLookup):
    strict = False


class AgeLookup(AbstractLookup):
    strict = False


class TrapTypeLookup(AbstractLookup):
    pass