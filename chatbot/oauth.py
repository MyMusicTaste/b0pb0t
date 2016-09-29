# -*- coding: utf8 -*-
import urllib2
import urllib
from multiprocessing.dummy import Pool
import json
from boto3.dynamodb.conditions import Key
from random import randint
import conf


def multi_run_wrapper(args):
    return send_request(*args)


def send_request(url, parameter):
    try:
        data = urllib.urlencode(parameter, doseq=True)

        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req).read()
        return response
    except Exception, e:
        print e
        raise Exception('Bad Request: %s' % e)


def get_phrase(key):
    phrases_table = conf.aws_dynamo_db.Table(conf.BOT_PHRASES)
    items = phrases_table.query(KeyConditionExpression=Key('Key').eq(key))['Items']
    if len(items) > 1:
        index = randint(0, len(items)-1)
        return items[index]['Phrase']
    else:
        phrase = items[0]['Phrase']
    return phrase


def lambda_handler(event, context):
    print event
    try:
        query_string = event['params']['querystring']

        code = query_string['code']
        state = query_string['state']
    except KeyError, e:
        print e
        raise Exception("Bad Request: Key error \"code\"")
    except Exception, e:
        print e
        raise Exception("Bad Request: %s" % e)

    payload = {'client_id': conf.CLIENT_ID, 'client_secret': conf.CLIENT_SECRET, 'code': code}
    response = send_request(url=conf.OAUTH_ACCESS, parameter=payload)
    print response

    if type(response) == str:
        response = json.loads(response)

    try:
        access_token = response['access_token']

        team_id = response['team_id']
        user_id = response['user_id']
        bot_dict = response['bot']
        bot_id = bot_dict['bot_user_id']
        bot_token = bot_dict['bot_access_token']

        team_table = conf.aws_dynamo_db.Table(conf.SLACK_TEAM_TABLE)
        team_table.put_item(Item={'Team_id': team_id, 'User_id': 'Team', 'Bot_access_token': bot_token, 'Bot_user_id': bot_id})
        team_table.put_item(Item={'Team_id': team_id, 'User_id': user_id, 'Access_token': access_token})

        if state == 'tutorial':
            user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
            response = user_table.get_item(Key={'User_id': user_id})
            print response

            payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true'}

            if 'Item' in response:
                item = response['Item']
                if 'Status' in item and item['Status'] == 'tutorial':
                    payload.update(make_tutorial_more_option_list())
                    send_request(conf.CHAT_POST_MESSAGE, payload)
        elif state == 'install':
            response = send_start_demo_message(user_id, bot_token)
            print 'app install %s' % response
        else:
            payload = {
                'token': bot_token,
                'channel': user_id,
                'as_user': 'true',
                'text': 'Thanks! Let\'s find a good restaurant!'
            }
            send_request(conf.CHAT_POST_MESSAGE, payload)

            payload = {
                'team_id': team_id,
                'event': {
                    'channel': user_id,
                    'user': user_id,
                    'ts': state,
                    'text': 'what to eat'
                }
            }

            conf.aws_sns.publish(
                TopicArn=conf.aws_sns_event_arn,
                Message=json.dumps({'default': json.dumps(payload)}),
                MessageStructure='json'
            )

        return 'Success'

    except KeyError, e:
        print e
        raise Exception("Bad Request: %s" % e)
    except Exception, e:
        print e
        raise Exception("Bad Request: %s" % e)


def im_open(members, bot_token):
    params = list()
    for member in members:
        url = 'https://slack.com/api/im.open'
        payload = {'token': bot_token, 'user': member}
        param = (url, payload)
        params.append(param)

    pool = Pool(4)
    results = pool.map(multi_run_wrapper, params)
    print results
    return results


def send_start_demo_message(user_id, bot_token):
    user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
    user_table.put_item(Item={'User_id': user_id, 'Status': 'tutorial'})

    attachment = [
        {
            'text': '#%s' % 'Simple demo',
            'color': '#3aa3e3',
            'attachment_type': 'default',
            'fallback': "simple_demo_start",
            'callback_id': "simple_demo_start",
            'actions': [
                {
                    'name': 'simple demo',
                    'text': 'simple demo',
                    'type': 'button',
                    'value': 'simple demo'
                }
            ]
        }
    ]
    attachment = json.dumps(attachment)

    phrase = get_phrase('tutorial_1')

    payload = {
        'channel': user_id,
        'token': bot_token,
        'text': phrase,
        'attachments': attachment,
        'as_user': 'true'
    }

    results = send_request(conf.CHAT_POST_MESSAGE, payload)
    return results


def make_tutorial_more_option_list():
    menu_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)
    response = menu_table.query(
        KeyConditionExpression=Key('Location').eq(conf.TUTORIAL_DEFAULT_RESTAURANT_LOCATION)
    )
    items = response['Items']

    menu_list = items[0:5]
    attachments = list()
    print
    for restaurant in menu_list:
        categories = restaurant['categories']
        categories_text = str()
        for index, category in enumerate(categories):
            if index < 3:
                if index == 0:
                    categories_text += category['name'].encode('utf8')
                else:
                    categories_text += ', ' + category['name'].encode('utf8')

        attachment = {
            'title': restaurant['name'].encode('utf8'),
            'title_link': restaurant['url'].encode('utf8'),
            'text': categories_text,
            'thumb_url': restaurant['image_url'].encode('utf8'),
            'color': '#3aa3e3'
        }
        attachments.append(attachment)

    action = {
        'name': 'More options',
        'text': 'More options',
        'type': 'button',
        'value': 'More options'
    }

    phrase = get_phrase('tutorial_3')
    button_attachment = {
        'text': phrase,
        'color': '#3aa3e3',
        'attachment_type': 'default',
        'fallback': "simple_demo_more_options",
        'callback_id': "simple_demo_more_options",
        'actions': [action]
    }
    attachments.append(button_attachment)

    attachments = json.dumps(attachments)

    payload = {
        'text': 'Thanks! Let\'s see how it works!',
        'attachments': attachments
    }
    return payload

