# -*- coding: utf8 -*-
import json
import urllib
import urlparse
from boto3.dynamodb.conditions import Key
from random import randint
import conf


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

    print json_dict['callback_id']
    callback = json_dict['callback_id']
    if callback == 'menu_event_general':
        text = json_dict['original_message']['text']
        attachments = json_dict['original_message']['attachments']

        user = json_dict['user']['id']

        vote_table = conf.aws_dynamo_db.Table(conf.VOTE_TABLE)
        response = vote_table.get_item(Key={'Message_ts': json_dict['message_ts'], 'User_id': user})
        if 'Item' not in response:
            attachments.append({'text': '<@%s> voted.' % user})

        payload = {'text': text, 'attachments': attachments}

        value = json_dict['actions'][0]['value']
        value = json.loads(value)

        vote_table.put_item(
            Item={
                'Message_ts': json_dict['message_ts'],
                'User_id': user,
                'Restaurant': json_dict['actions'][0]['name'],
                'Meta': value
            }
        )
        return payload

    elif callback == 'simple_demo_start':
        team_table = conf.aws_dynamo_db.Table(conf.SLACK_TEAM_TABLE)
        response = team_table.get_item(Key={'Team_id': json_dict['team']['id'], 'User_id': json_dict['user']['id']})
        item = response['Item']

        text = json_dict['original_message']['text']
        if 'Access_token' not in item:
            phrase = get_phrase('tutorial_auth')
            text += '\n\n' + phrase

            return {
                'text': text, 'attachments': [
                    {
                        'title': 'Authorization',
                        'title_link': 'https://slack.com/oauth/authorize?scope=bot,channels:write,im:write,im:history,reminders:write&state=%s&client_id=%s' % ('tutorial', conf.CLIENT_ID)
                    }
                ]
            }
        else:
            return {
                'text': text, 'attachments': [
                    {
                        'text': '#Simple demo\n:white_check_mark: simple demo'
                    }
                ]
            }

    elif callback == 'simple_demo_send_the_poll':
        user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
        user_table.put_item(Item={'User_id': json_dict['user']['id']})

        phrase = get_phrase('tutorial_5')

        origin_attachments = json_dict['original_message']['attachments']

        attachments = list()
        for attachment in origin_attachments:
            if 'actions' in attachment:
                attachment['actions'] = []
                if 'text' in attachment:
                    attachment['text'] = attachment['text']+'\n:white_check_mark: ' + json_dict['actions'][0]['name']
                else:
                    attachment['text'] = '\n:white_check_mark: ' + json_dict['actions'][0]['name']
            attachments.append(attachment)

        attachments.append({'text': phrase})

        text = json_dict['original_message']['text']
        return {'text': text, 'attachments': attachments}

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


def get_phrase(key):
    phrases_table = conf.aws_dynamo_db.Table(conf.BOT_PHRASES)
    items = phrases_table.query(KeyConditionExpression=Key('Key').eq(key))['Items']
    if len(items) > 1:
        index = randint(0, len(items)-1)
        return items[index]['Phrase'].encode('utf8')
    else:
        phrase = items[0]['Phrase'].encode('utf8')
    return phrase