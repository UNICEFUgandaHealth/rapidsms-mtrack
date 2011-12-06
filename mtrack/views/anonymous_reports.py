from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from mtrack.models import AnonymousReport
from mtrack.forms import EditAnonymousReportForm
from generic.views import generic_row
from django.template import RequestContext


@login_required
def delete_report(request, report_pk):
    report = get_object_or_404(AnonymousReport, pk=report_pk)
    if request.method == 'POST':
        report.delete()
    return HttpResponse(status=200)


@login_required
def edit_report(req, anonymous_report_pk):
    anonymous_report = get_object_or_404(AnonymousReport, pk=anonymous_report_pk)
    edit_report_form = EditAnonymousReportForm(instance=anonymous_report)
    if req.method == 'POST':
        edit_report_form = AnonymousEditReportForm(instance=anonymous_report, data=request.POST)
        if edit_report_form.is_valid:
            edit_report_form.save()
        else:
            return render_to_response('mtrack/partials/anon_edit_row.html',
                    {'report_form':edit_report_form, 'anonymous_report':anonymous_report}, context_instance=RequestContext(req))
        return render_to_response('mtrack/partials/anon_row.html',
                {'object':AnonymousReport.objects.get(pk=anonymous_report_pk),'selectable':True}, context_instance=RequestContext(req))
    else:
        return render_to_response('mtrack/partials/anon_edit_row.html',
                {'report_form':edit_report_form, 'anonysmous_report':anonymous_report},context_instance=RequestContext(req))