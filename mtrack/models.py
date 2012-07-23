from django.db import models
from healthmodels.models.HealthFacility import HealthFacility
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection
from rapidsms_httprouter.models import Message
from rapidsms_xforms.models import XFormSubmission

ACTIONS = (
    ('Op', 'Open'),
    ('C', 'Claim'),
    ('Es', 'Escalate'),
    ('Cl', 'Close'),
    ('Ig', 'Ignore'),
    #('Na', 'No Action needed'),
    #('S', 'Stock out'),
    #('Ot', 'Other critical')
)
TOPICS = (
          ('Absenteeism', 'Absenteeism'),
          ('Drug Theft', 'Drug Theft'),
          ('Extortion', 'Extortion'),
          ('Fraud', 'Fraud'),
          ('General Complaint', 'General Complaint'),
          ('General Inquiry', 'General Inquiry'),
          ('Good Service', 'Good Service'),
          ('Ignore/Delete', 'Ignore/Delete'),
          ('Illegal schools', 'Illegal Schools'),
          ('Impersonation', 'Impersonation'),
          ('Malpractice', 'Malpractice'),
          ('Negligence', 'Negligence'),
          ('Other Critical', 'Other Critical'),
          ('Stock Out', 'Stock Out'),
          ('Unknown', 'Unknown'),
          ('Working hours of HCs', 'Working hours of HCs'),
        )
ACTION_CENTERS = (
                  ('MOH', 'MOH'),
                  ('MU', 'MU'),
                  ('NMS', 'NMS'),
                  )
class AnonymousReport(models.Model):
    connection = models.ForeignKey(Connection)
    messages = models.ManyToManyField(Message, null=True, default=None)
    date = models.DateTimeField(auto_now_add=True)
    district = models.ForeignKey(Location, null=True)
    comments = models.TextField(null=True)
    health_facility = models.ForeignKey(HealthFacility, null=True)
    action = models.CharField(max_length=2, choices=ACTIONS, default='Op') #is this the right way??
    topic = models.CharField(max_length=32, default='Unknown', choices=TOPICS, null=True)
    action_center = models.CharField(max_length=32, default='', choices=ACTION_CENTERS, null=True)
    action_taken = models.TextField(null=True)
    def __unicode__(self):
        return self.connection.identity

    class Meta:
        ordering = ['-date', 'action', 'topic']

#class AnonymousReportBatch(models.Model):
#    connection = models.ForeignKey(Connection)
#    anonymous_reports = models.ManyToManyField(AnonymousReport, null=True, default=None)
#    date = models.DateTimeField(auto_now_add=True)

#Use this model to store extra info on submission esp those created from dashboard
class XFormSubmissionExtras(models.Model):
    submission = models.ForeignKey(XFormSubmission)
    is_late_report = models.BooleanField(default=False)
    submitted_by = models.TextField(null=True)
    cdate = models.DateTimeField(auto_now_add=True) #since we fake submission.created

    class Meta:
        db_table = 'rapidsms_xforms_xformsubmissionextras'
import signals
