# Define your custom views here or overwrite the default views. Default
# CRUD operations are generated by the ringo frameworkd.
from pyramid.response import Response
from ringo.views.request import (
    handle_params,
    handle_history,
    get_item_from_request
)
from ringo.views.base import web_action_view_mapping
from ringo.views.base.list_ import bundle_request_handlers


def evaluate(request):
    handle_history(request)
    handle_params(request)
    #item = get_item_from_request(request)
    rvalue = _handle_export_request(request, [])
    return Response("OK")


def _handle_export_request(request, items):
    return Response("OK")
    return {}


# Register the view and request handlers.
web_action_view_mapping["evaluate"] = evaluate
bundle_request_handlers["evaluate"] = _handle_export_request