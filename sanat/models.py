from django.db import models

# Create your models here.

from django.conf import settings
from django.utils import timezone

class WordStatus(models.Model):
    class Meta:
        index_together = [["lid", "wlid"],
                         ]
    wid = models.IntegerField(primary_key=True)
    lid = models.IntegerField(null=True, blank=True)    # list ID
    wlid = models.IntegerField(null=True, blank=True)   # word ID within the list
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    last_ts = models.DateTimeField()
    last_c_ts = models.DateTimeField()
    last_seq = models.IntegerField()
    last_c_seq = models.IntegerField()
    c_short = models.FloatField()   # short term exponential moving average
    c_med = models.FloatField()     # medium
    c_long = models.FloatField()    # long

    def answer(self, is_correct):
        is_correct = int(bool(is_correct))
        s = .5
        m = .2
        l = .1
        self.c_short = s*is_correct + (1-s)*self.c_short
        self.c_med   = m*is_correct + (1-m)*self.c_med
        self.c_long  = l*is_correct + (1-l)*self.c_long
        self.last_ts = timezone.non()
        if ans:
            self.last_c_ts = timezone.non()
        max_seq = self.objects.aggregate(models.Max('last_seq'))['max']
        self.last_seq = max_seq + 1
        if correct:
            self.last_c_seq = max_seq + 1

class Answer(models.Model):
    aid = models.IntegerField(primary_key=True) # answer ID
    # user ID
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    #uid = db.relationship(User, backref='answers', lazy='dynamic')
    sid = models.IntegerField()                   # session ID
    lid = models.IntegerField(null=True, blank=True) # list ID
    wlid = models.IntegerField(null=True, blank=True)
    ts = models.DateTimeField(auto_now_add=True)
    q = models.CharField(max_length=256)
    a = models.CharField(max_length=256)
    c = models.CharField(max_length=256)
    correct = models.FloatField()


class Hint(models.Model):
    hid  = models.IntegerField(primary_key=True)
    ts   = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    #uid = db.relationship(User, backref='answers', lazy='dynamic')
    lid  = models.IntegerField()                  # list ID
    wlid = models.IntegerField()
    q    = models.CharField(max_length=256)
    hint = models.CharField(max_length=256)
