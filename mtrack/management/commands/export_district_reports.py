from django.core.management.base import BaseCommand
import traceback
import os
from script.models import ScriptSession
from mtrack.settings import MTRACK_ROOT
from rapidsms.models import Contact
from django.utils.datastructures import SortedDict
from healthmodels.models import HealthProvider
from rapidsms_httprouter.models import Message
from django.db.models import Count
from poll.models import Poll
import datetime
from uganda_common.utils import ExcelResponse
from cvs.templatetags.stats_extras import get_district
from rapidsms_xforms.models import XFormSubmission, XFormField
from rapidsms.contrib.locations.models import Location


class Command(BaseCommand):
    """Generates District Reports"""
    districts = Location.objects.filter(type='district').values('pk', 'name')
    def handle(self, **options):
        try:
            for l in self.districts:
                reports = XFormSubmission.objects.exclude(connection=None).filter(xform__keyword__in=['com', 'mal', 'rutf', 'epi', 'home', 'birth', 'muac', 'opd', 'test', 'treat', 'rdt', 'act', 'qun', 'cases', 'death'])
                reports = reports.exclude(connection__contact=None).\
                exclude(connection__contact__reporting_location=None).\
                filter(connection__contact__reporting_location__in=Location.objects.get(pk=l['pk']).\
                       get_descendants(include_self=True).values_list('pk', flat=True))
                excel_file_path = os.path.join(os.path.join(os.path.join(MTRACK_ROOT, 'static'), 'spreadsheets'), 'reports_%s.xls' % (l['name'].capitalize()))
                if not reports:
                    continue
                export_data_list = []
                for r in reports:
                    print "adding %d for %s" % (r.pk, l['name'])
                    export_data = SortedDict()
                    export_data['report_id'] = r.pk
                    export_data['report'] = r.xform.name
                    export_data['date'] = str(r.created)
                    export_data['reporter'] = r.connection.contact.name if r.connection.contact else 'None'
                    export_data['reporter_id'] = r.connection.contact.pk if r.connection.contact else 'None'
                    export_data['phone'] = r.connection.identity
                    #district = str(get_district(r.connection.contact.reporting_location) if r.connection.contact else 'None')

                    export_data['district'] = l['name']
                    export_data['facility'] = str(r.connection.contact.healthproviderbase.facility) if (r.connection.contact and r.connection.contact.healthproviderbase) else 'None'
                    export_data['village'] = str(r.connection.contact.village or r.connection.contact.reporting_location) if r.connection.contact else 'None'
                    export_data['valid'] = (r.has_errors and "No") or "Yes"
                    for f in XFormField.objects.order_by('slug'):
                        export_data["%s:%s" % (f.xform.name, f.description)] = getattr(r.eav, f.slug) or 'None'

                    export_data_list.append(export_data)
                ExcelResponse(export_data_list, output_name=excel_file_path, write_to_file=True)

            print "finished!"
        except Exception, exc:
            print traceback.format_exc(exc)
