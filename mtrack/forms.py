from django import forms
from healthmodels.models.HealthFacility import HealthFacility, HealthFacilityType
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection
from contact.models import MassText
from rapidsms_httprouter.models import Message
from .models import AnonymousReport
from generic.forms import ActionForm
from uganda_common.forms import SMSInput
from django.conf import settings
from django.contrib.sites.models import Site

class FacilityResponseForm(forms.Form):
    def __init__(self, data=None, **kwargs):
        response = kwargs.pop('response')
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)

    value = forms.ModelChoiceField(queryset=HealthFacility.objects.order_by('name'))

class DistrictResponseForm(forms.Form):
    def __init__(self, data=None, **kwargs):
        response = kwargs.pop('response')
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)

    value = forms.ModelChoiceField(queryset=Location.objects.order_by('name'))


class FacilityForm(forms.Form):
    """
    How we handle an anonymous "complaint" or "report"
    """
    name = forms.CharField(max_length=100, required=True)
    code = forms.CharField(max_length=50, required=False)
    type = forms.ModelChoiceField(queryset=HealthFacilityType.objects.all(), required=True)
    catchment_areas = forms.ModelMultipleChoiceField(queryset=Location.objects.all(), required=False)
    facility_district = forms.ModelChoiceField(queryset=Location.objects.filter(type__name='district').order_by('name'), empty_label='----', required=False, \
                                      widget=forms.Select({'onchange':'update_facility_district(this)'}))
    


    def __init__(self, *args, **kwargs):
        self.facility = kwargs.pop('instance')
        if not 'data' in kwargs:
            initial = { \
                'name':self.facility.name, \
                'code':self.facility.code, \
                'type':self.facility.type, \
                'catchment_areas':self.facility.catchment_areas.all(), \
            }
            district = get_district_for_facility(self.facility)
            if district:
                initial.update({'facility_district':district})
            kwargs.update({'initial':initial})
        forms.Form.__init__(self, *args, **kwargs)

    def save(self):
        cleaned_data = self.cleaned_data
        self.facility.name = cleaned_data.get('name')
        self.facility.code = cleaned_data.get('code')
        self.facility.type = cleaned_data.get('type')
        self.facility.save()

        self.facility.catchment_areas.clear()
        for c in cleaned_data.get('catchment_areas'):
            self.facility.catchment_areas.add(c)
        return


class EditAnonymousReportForm(forms.ModelForm):
    """
	We can now edit any reports that come in anonymously
	"""
#    def __init__(self, *args, **kwargs):
#        super(EditAnonymousReportForm, self).__init__(*args, **kwargs)
#        self.fields['district'] = TreeNodeChoiceField(queryset=self.fields['district'].queryset, level_indicator=u'.')

    class Meta:
        model = AnonymousReport
#        fields = ('health_facility', 'district', 'messages', 'comments' )

class MassTextForm(ActionForm):
    text = forms.CharField(max_length=160, required=True, widget=SMSInput())
    action_label = "Send Message"

    def clean_text(self):
        text = self.clean_data['text']
        for find, replace in [
            (u'\u201c', '"'),
            (u'\u201d', '"'),
            (u'\u201f', '"'),
            (u'\u2018', "'"),
            (u'\u2019', "'"),
            (u'\u201B', "'"),
            (u'\u2013', "-"),
            (u'\u2014', "-"),
            (u'\u2015', "-"),
            (u'\xa7', "$"),
            (u'\xa1', "i"),
            (u'\xa4', ''),
            (u'\xc4', 'A')
        ]:
            text = text.replace(find, replace)
        return text
    
    def perform(self, request, results):
        if results is None or len(results) == 0:
            return ('A message must have one or more recipients!', 'error',)
        if request.user and request.user.has_perm('auth.add_message'):
            connections = list(Connection.objects.filter(contact__in=results).distint())
            text = self.cleaned_data.get('text', "")
            text = text.replace("%", u'\u0025')

            messages = Message.mass_text(text, connections)

            MassText.bulk.bulk_insert(send_pre_save=False,user=request.user,text=text,contacts=list(results))
            masstexts = MassText.bulk.bulk_insert_commit(send_post_save=False, autoclobber=True)
            masstext = masstexts[0]

            if settings.SITE_ID:
                masstext.sites.add(Site.objects.get_current())

            return ("Message successfully sent to %d numbers" % len(connections), 'success',)
        else:
            return ("You don't have permission to send messages!", "error",)
                
            