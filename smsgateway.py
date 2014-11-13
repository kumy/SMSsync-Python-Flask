import json

from flask import Flask
from flask import request
from flask import make_response
from flask import jsonify
from flask.ext import restful

from uuid import uuid4

secret = 'mysecret'

messages_pending = []
messages_waiting = []
messages_sent    = []


app = Flask(__name__)
api = restful.Api(app)

class SMS(dict):
    """ Basic SMS Object """
    __allowed = ('to', 'message', 'uuid')

    def __init__(self, to, message):
        self['to']      = to
        self['message'] = message
        self['uuid']    = str(uuid4())

    def __setitem__(self, k, v):
        if k not in self.__allowed:
            raise KeyError('key not allowed: %s' % k)
        return super(SMS, self).__setitem__(k, v)


class DeliveryReport(dict):
    """ Delivery Reports """
    __allowed = ('uuid', 'sent_result_code', 'sent_result_message', 'delivered_result_code', 'delivered_result_message')

    def __init__(self, report):
        self.update(report)

    def __setitem__(self, k, v):
        if k not in self.__allowed:
            raise KeyError('key not allowed: %s' % k)
        return super(SMS, self).__setitem__(k, v)


class SMSSync(restful.Resource):
    """ Main API """

    def post(self):
        """ Process the POSTs requests """
        task = request.args.get('task')
        if task == "sent":
            """ Taking message to send """
            data = { 'message_uuids': [] }
            response = request.get_json()

            if response and 'queued_messages' in response:
                for uuid in response['queued_messages']:
                    for sms in messages_pending:
                        if uuid == sms['uuid']:
                            messages_waiting.append(sms)
                            messages_pending.remove(sms)
                            data['message_uuids'].append(uuid)

            return jsonify(data)
        elif task == "result":
            """
            Dealing with Delivery reports
            Getting waiting list
            """
            data = { 'message_uuids': [] }
            response = request.get_json()

            if response and 'message_results' in response:
                for report in response['message_results']:
                    uuid = report['uuid']
                    for sms in messages_waiting:
                        if uuid == sms['uuid']:
                            messages_waiting.remove(sms)
                            data['message_uuids'].append(uuid)
            return jsonify(data)
        else:
            """ Submit New SMS """
            to      = request.form.get('to')
            message = request.form.get('message')
            sms = SMS(to, message)
            messages_pending.append(sms)
            return jsonify(sms)

    def get(self):
        """ Process the GETs requests """
        """ Taking message to send """
        task = request.args.get('task')

        if task == "send":
            data = {
                'payload': {
                    'task': task,
                    'secret': secret,
                    'messages': messages_pending
                    }
                }
            return jsonify(data)
        elif task == "result":
            """
            Dealing with Delivery reports
            Getting waiting list
            """
            data = { 'message_uuids': [] }
            for sms in messages_waiting:
                data['message_uuids'].append(sms['uuid'])
            return jsonify(data)


api.add_resource(SMSSync, '/smssync')

if __name__ == '__main__':

    app.run(debug=True, host="0.0.0.0")
