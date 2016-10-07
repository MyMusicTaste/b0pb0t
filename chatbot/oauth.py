# -*- coding: utf8 -*-
import json
import conf
import bopbot_util
import bopbot_tutorial
from database_manager import BopBotDatabase


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
    response = bopbot_util.send_request(url=conf.OAUTH_ACCESS, parameter=payload)
    print response

    if type(response) == str:
        response = json.loads(response)

    try:
        if not response['success']:
            print 'send request failed: %s' % response['result']
            raise Exception("Bad Request: %s" % response['result'])

        response = response['result']

        if type(response) == str:
            response = json.loads(response)

        access_token = response['access_token']

        team_id = response['team_id']
        user_id = response['user_id']
        bot_dict = response['bot']
        bot_id = bot_dict['bot_user_id']
        bot_token = bot_dict['bot_access_token']

        team_table = BopBotDatabase(table=conf.SLACK_TEAM_TABLE)
        team_table.put_item_to_table(item={'Team_id': team_id, 'User_id': 'Team', 'Bot_access_token': bot_token, 'Bot_user_id': bot_id})
        team_table.put_item_to_table(item={'Team_id': team_id, 'User_id': user_id, 'Access_token': access_token})

        if state == 'tutorial':
            user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
            response = user_table.get_item(Key={'User_id': user_id})
            print response

            if 'Item' in response:
                item = response['Item']
                if 'Status' in item and item['Status'] == 'tutorial':
                    bopbot_tutorial.clicked_simple_demo_start(team_id=team_id, user_id=user_id, bot_token=bot_token)

        elif state == 'install':
            install_im_open(bot_token=bot_token)
            response = bopbot_tutorial.send_start_demo_message(user_id=user_id, bot_token=bot_token)
            print 'app install %s' % response

        else:
            phrase = bopbot_util.get_phrase('main_auth_success')
            payload = bopbot_util.get_dict_for_slack_post_request(token=bot_token, channel=user_id, text=phrase)
            bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)

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


def install_im_open(bot_token):
    payload = {'token': bot_token, 'exclude_archived': 1}
    url = 'https://slack.com/api/channels.list'
    response = bopbot_util.send_request(url, payload)
    response = response['result']
    response = json.loads(response)

    try:
        channels = response['channels']
        for channel in channels:
            if channel['is_general']:
                channel_id = channel['id']
                url = 'https://slack.com/api/channels.info'
                response = bopbot_util.send_request(url, {'token': bot_token, 'channel': channel_id})
                result = response['result']
                result = json.loads(result)
                print result

                channel = result['channel']
                members = channel['members']

                params = []
                url = 'https://slack.com/api/im.open'
                for member in members:
                    payload = {'token': bot_token, 'user': member}
                    param = (url, payload)
                    params.append(param)

                return bopbot_util.send_request_with_multiprocessing_pool(4, params)
    except Exception, e:
        print e

    return
