# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import opentracing
import flask


app = flask.Flask('MyFlaskApplication')


@app.route('/hello/<username>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def my_route(username):
    span = opentracing.tracer.scope_manager.active.span
    span.set_tag('handled', 'tag')
    return 'Hello, {}!'.format(username)


bp = flask.Blueprint('MyBlueprint', 'MyFlaskApplication')


@bp.route('/<page>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def my_blueprint_route(page):
    span = opentracing.tracer.scope_manager.active.span
    span.set_tag('handled', 'tag')
    return 'Rendering {}'.format(page)


app.register_blueprint(bp, url_prefix='/bp')
