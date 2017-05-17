# Define your custom views here or overwrite the default views. Default
# CRUD operations are generated by the ringo frameworkd.
import os
import logging
import ezodf
import mimetypes
from tempfile import NamedTemporaryFile
from datetime import datetime
from ringo.views.request import (
    handle_params,
    handle_history,
    is_confirmed,
    get_item_from_request
)
from ringo.lib.helpers.appinfo import get_app_location
from ringo.lib.helpers.format import get_local_datetime
# from ringo.lib.odfconv import get_converter
from ringo.views.base.create import create
from ringo.views.base.update import update
from ringo.views.base import set_web_action_view
from ringo.views.base.list_ import set_bundle_action_handler
from ringo_evaluation.lib.renderer import EvaluationDialogRenderer
from ringo_evaluation.model import Extension
from ringo_evaluation.lib.export import RecursiveRelationExporter

log = logging.getLogger(__name__)

def _convert_spreadsheet(spreadsheet, format):
    converter = get_converter()
    data = converter.convert(spreadsheet.tobytes(), "ods", update=True)
    if format == "pdf":
        tmp = NamedTemporaryFile()
        tmp.write(data)
        tmp.seek(0)
        dummy = ezodf.opendoc(tmp.name)
        for i in range(1, len(dummy.sheets)):
            del dummy.sheets[-1]
        data = converter.convert(dummy.tobytes(), "ods", update=False)
        tmp.close()
    data = converter.convert(data, format, update=False)
    return data

def _get_upload_dir(appname):
    applocation = get_app_location(appname)
    uploaddir = os.path.join(applocation, appname, "uploads", "ringo_evaluation")
    return uploaddir


def _write_file(filename, data):
    output_file = open(filename, 'wb')
    output_file.write(data)
    output_file.close()


def save_file(request, item):
    """Helper function which is called after the validation of the form
    succeeds. The function will get the data from the file from the
    request and set it in the model including size and mime type.
    Addiotionally it will set the filename based on the uploaded file if
    no other name is given."""
    try:
        # Rewind file
        # Get application name:
        appname = request.registry.__name__
        uploaddir = _get_upload_dir(appname)
        if not os.path.exists(uploaddir):
            os.makedirs(uploaddir)

        request.POST.get('file').file.seek(0)
        data = request.POST.get('file').file.read()
        # Filname must be encoded as str as tem.data is byte and
        # automatic conversion from unicode to byte fails at least for
        # postgres.
        filename = request.POST.get('file').filename.encode('ascii', 'ignore')
        filename = os.path.join(uploaddir, filename)
        item.data = filename
        item.size = len(data)
        item.mime = mimetypes.guess_type(filename)[0]
        _write_file(os.path.join(filename), data)
    except AttributeError:
        # Will be raised if the user submits no file.
        pass
    return item


def create_(request):
    return create(request, callback=save_file)


def update_(request):
    return update(request, callback=save_file)


def evaluate(request):
    handle_history(request)
    handle_params(request)
    item = get_item_from_request(request)
    return _handle_evaluation_request(request, [item])


def load_file(data):
    if data.startswith("@"):
        # Load the data from the filesystem.
        # Path is @package:/path/to/file/relative/to/package/file
        app = get_app_location(data.split(":")[0].strip("@"))
        rel_path = data.split(":")[1]
        data = os.path.join(app, rel_path)
    return data


def _handle_evaluation_request(request, items, context=None):
    # context is always None if comming from Ringo.
    clazz = request.context.__model__
    modul = request.context.__modul__
    renderer = EvaluationDialogRenderer(request, clazz)
    form = renderer.form
    if (request.method == 'POST'
       and is_confirmed(request)
       and form.validate(request.params)):
        # 1. Load evaluation file
        factory = Extension.get_item_factory()
        evaluation = factory.load(form.data["evaluations"])
        exportformat = form.data.get("exportformat", "ods")
        export_config = evaluation.configuration
        spreadsheet = ezodf.opendoc(load_file(evaluation.data))

        # 2. Export data
        exporter = RecursiveRelationExporter(clazz, export_config)
        sheet_data = exporter.perform(items)
        relation_config = exporter.get_relation_config()

        # 3. Create sheets per relation
        sheets = spreadsheet.sheets
        for relation in relation_config:
            data = sheet_data[relation]
            if relation == "root":
                sheetname = modul.name
            else:
                sheetname = relation
            try:
                sheet = sheets[sheetname]
            except:
                sheets.append(ezodf.Table(sheetname))
                sheet = sheets[sheetname]
            _fill_sheet(sheet, data, relation_config[relation])

        # 4. Convert and recalcualte the spreadsheet
        # converter = get_converter()
        # if converter.is_available():
        #     spreadsheet_data = _convert_spreadsheet(spreadsheet, exportformat)
        # else:
        spreadsheet_data = spreadsheet.tobytes()

        # 5. Build response
        resp = request.response
        resp.content_type = str('application/%s' % exportformat)
        ctime = get_local_datetime(datetime.utcnow())
        filename = "%s_%s.%s" % (ctime.strftime("%Y-%m-%d-%H%M"),
                                 sheetname.lower(),
                                 exportformat)
        resp.content_disposition = 'attachment; filename=%s' % filename
        resp.body = spreadsheet_data
        return resp
    else:
        # FIXME: Get the ActionItem here and provide this in the Dialog to get
        # the translation working (torsten) <2013-07-10 09:32>
        rvalue = {}
        rvalue['dialog'] = renderer.render(items)
        return rvalue


def _fill_sheet(sheet, data, fields):
    if len(data) > 0:
        if not fields:
            fields = sorted(data[0].keys())
    sheet.reset(size=(len(data)+1, len(fields)))
    for x, field in enumerate(fields):
        cell = sheet[0,x]
        cell.set_value(field)
    for y, item in enumerate(data):
        for x, field in enumerate(fields):
            cell = sheet[y+1, x]
            if field in item:
                cell.set_value(item[field] or "")

# Register the view and request handlers.
# Overwrite create and update view specificially for the evaluation
# module
set_web_action_view("create", create_, "evaluations")
set_web_action_view("update", update_, "evaluations")
# Add generic evaluation view for all modules
set_web_action_view("evaluate", evaluate)
set_bundle_action_handler("evaluate", _handle_evaluation_request)
