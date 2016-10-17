# -*- coding: utf8 -*-
import json
import conf
import bopbot_util
import bopbot_tutorial
from database_manager import BopBotDatabase


def lambda_handler(event, context):
    print event
    query_string = event['params']['querystring']

    code = query_string['code']
    state = query_string['state']

    payload = {'client_id': conf.CLIENT_ID, 'client_secret': conf.CLIENT_SECRET, 'code': code}
    response = bopbot_util.send_request_to_slack(url=conf.OAUTH_ACCESS, parameter=payload)
    print response

    if not response:
        print 'send request failed'
        raise Exception("Bad Request")

    if type(response) == str:
        response = json.loads(response)

    try:
        access_token = response['access_token']
        team_id = response['team_id']
        team_name = response['team_name']
        user_id = response['user_id']
        bot_dict = response['bot']
        bot_id = bot_dict['bot_user_id']
        bot_token = bot_dict['bot_access_token']
    except KeyError, e:
        print e
        print 'Response: %s' % response
        raise Exception("Bad Request: %s" % e)
    except Exception, e:
        print e
        print 'Response: %s' % response
        raise Exception("Bad Request: %s" % e)

    team_table = BopBotDatabase(table=conf.SLACK_TEAM_TABLE)
    team_table.put_item_to_table(item={'Team_id': team_id, 'User_id': 'Team', 'Team_name': team_name, 'Bot_access_token': bot_token, 'Bot_user_id': bot_id})
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
        bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)

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


def install_im_open(bot_token):
    payload = {'token': bot_token, 'exclude_archived': 1}
    url = 'https://slack.com/api/channels.list'

    response = bopbot_util.send_request_to_slack(url=url, parameter=payload)
    if not response:
        print 'Get slack channel list failed'
        return

    # response = json.loads(response)

    try:
        channels = response['channels']
        for channel in channels:
            if channel['is_general']:
                channel_id = channel['id']
                url = 'https://slack.com/api/channels.info'
                payload = {'token': bot_token, 'channel': channel_id}
                response = bopbot_util.send_request_to_slack(url=url, parameter=payload)

                if not response:
                    return

                # response = json.loads(response)

                channel = response['channel']
                members = channel['members']

                params = []
                url = 'https://slack.com/api/im.open'
                for member in members:
                    payload = {'token': bot_token, 'user': member}
                    param = (url, payload)
                    params.append(param)

                return bopbot_util.send_request_with_multiprocessing_pool(4, params)
    except Exception, e:
        print 'IM open failed %s' % e

    return
