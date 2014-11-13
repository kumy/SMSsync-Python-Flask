import json

from flask import Flask
from flask import request
from flask import make_response
from flask import jsonify
from flask.ext import restful

from uuid import uuid4

secret = 'mysecret'
messages = []


class SMSJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SMS):
            print obj
            return obj.sms
        return obj

app = Flask(__name__)
app.json_encoder = SMSJsonEncoder
api = restful.Api(app)

class SMS(object):
    """ Basic SMS Object """

    sms = {
        "to"     : None,
        "message": None,
        "uuid"   : None
        }

    def __init__(self, to, message):
        self.sms['to']      = to
        self.sms['message'] = message
        self.sms['uuid']    = str(uuid4())


class SMSSync(restful.Resource):
    def post(self):
	task = request.args.get('task')
        if task == "sent":
            data = { 'message_uuids': [] }
            response = request.get_json()

            if response and 'queued_messages' in response:
                data['message_uuids'] = response['queued_messages']

            for uuid in data['message_uuids']:
                for sms in messages:
                    if uuid == sms.sms.uuid:
                        messages.remove(sms)

	    return jsonify(data)
        else:
            to      = request.form.get('to')
            message = request.form.get('message')
            sms = SMS(to, message)
            messages.append(sms)
	    return jsonify(sms.sms)

    def get(self):
        task = request.args.get('task')

        data = {
            'payload': {
                'task': task,
                'secret': secret,
                'messages': messages
                }
            }
	return jsonify(data)

api.add_resource(SMSSync, '/smssync')

if __name__ == '__main__':

    app.run(debug=True, host="0.0.0.0")
