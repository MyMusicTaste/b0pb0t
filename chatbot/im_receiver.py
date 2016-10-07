# -*- coding: utf8 -*-
import json
import urllib
import urlparse

import conf
from database_manager import BopBotDatabase


def lambda_handler(event, context):
    try:
        body_dict = event['body-json']
        payload = str(urllib.unwrap(body_dict))
        payload = urlparse.parse_qs(payload)
        payload_dict = payload['payload'][0]

        json_dict = json.loads(payload_dict)

    except Exception, e:
        print event
        print e
        print 'event parsing error'
        raise Exception("Bad Request: request failed")

    try:
        print event
        response = conf.aws_sns.publish(
            TopicArn=conf.aws_sns_im_arn,
            Message=json.dumps({'default': json.dumps(event)}),
            MessageStructure='json'
        )
        print response
    except:
        raise Exception("Bad Request: request failed")

    callback = json_dict['callback_id']
    if callback == 'menu_event_general':
        text = json_dict['original_message']['text']
        attachments = json_dict['original_message']['attachments']

        user = json_dict['user']['id']
        vote_table = BopBotDatabase(table=conf.VOTE_TABLE)
        item = vote_table.get_item_from_table(key={'Message_ts': json_dict['message_ts'], 'User_id': user})
        if not item:
            attachments.append({'text': '<@%s> voted.' % user})

        payload = {'text': text, 'attachments': attachments}

        value = json_dict['actions'][0]['value']
        value = json.loads(value)

        vote_table.put_item_to_table(
            item={
                'Message_ts': json_dict['message_ts'],
                'User_id': user,
                'Restaurant': json_dict['actions'][0]['name'],
                'Meta': value
            }
        )
        return payload

    else:
        text = json_dict['original_message']['text']

        attachments = list()
        for attachment in json_dict['original_message']['attachments']:
            if 'actions' in attachment:
                attachment['actions'] = []
                if 'text' in attachment:
                    attachment['text'] = attachment['text']+'\n:white_check_mark: ' + json_dict['actions'][0]['name']
                else:
                    attachment['text'] = '\n:white_check_mark: ' + json_dict['actions'][0]['name']
            attachments.append(attachment)

        return {'text': text, 'attachments': attachments}
