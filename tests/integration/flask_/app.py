# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import opentracing
import flask

from signalfx_tracing import trace

app = flask.Flask('MyFlaskApplication')


@app.route('/hello/<username>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def my_route(username):
    span = opentracing.tracer.scope_manager.active.span
    span.set_tag('handled', 'tag')
    return 'Hello, {}!'.format(username)


@trace('myTracedHelper', tags=dict(one=1, two=2))
def my_traced_helper():
    return True


@app.route('/traced', methods=['GET'])
def my_traced_route():
    span = opentracing.tracer.scope_manager.active.span
    span.set_tag('handled', 'tag')
    my_traced_helper()
    return 'Traced!'


bp = flask.Blueprint('MyBlueprint', 'MyFlaskApplication')


@bp.route('/<page>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def my_blueprint_route(page):
    span = opentracing.tracer.scope_manager.active.span
    span.set_tag('handled', 'tag')
    return 'Rendering {}'.format(page)


app.register_blueprint(bp, url_prefix='/bp')
