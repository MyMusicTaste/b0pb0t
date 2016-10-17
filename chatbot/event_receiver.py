# -*- coding: utf8 -*-
import json
import conf


def lambda_handler(event, context):
    print event

    eq_body = event['body']
    if 'type' in eq_body:
        if eq_body['type'] == 'url_verification':
            challenge = eq_body['challenge']
            return {'challenge': challenge}

    print eq_body

    try:
        if eq_body['token'] != conf.VERIFY_TOKEN:
            return

        payload = eq_body
        response = conf.aws_sns.publish(
            TopicArn=conf.aws_sns_event_arn,
            Message=json.dumps({'default': json.dumps(payload)}),
            MessageStructure='json'
        )

        print response
        return {}
    except:
        raise Exception("Bad Request: request failed")

