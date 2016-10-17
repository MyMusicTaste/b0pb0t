# -*- coding: utf8 -*-
import json
import urllib
import urllib2
from boto3.dynamodb.conditions import Key, Attr
import time
from random import randint
import conf
import bopbot_util
from database_manager import BopBotDatabase


def lambda_handler(event, context):
    # TODO implement
    print event

    try:
        record = event['Records'][0]
        message = record['Sns']['Message']
        if type(message) is not dict:
            message = json.loads(message)

    except KeyError, e:
        raise Exception('Bad Request: Key error: %s' % e)
    except Exception, e:
        raise Exception('Bad Request: Exception: %s' % e)

    remain_time = int(message['time'])
    response = message['response']
    # response = json.loads(response)
    message_ts = response['message']['ts']
    channel_id = message['channel']
    channel_name = message['channel_name']
    user_id = message['user_id']
    bot_token = message['bot_token']

    # remain_time = 10
    time.sleep(60)
    if remain_time <= 60:
        return complete_poll_event(response, message_ts, channel_id, channel_name, bot_token, user_id)
    else:
        new_time = remain_time - 60

        text = '%s minute' % (new_time/60)
        if new_time/60 > 1:
            text += 's'
        text += ' left'

        payload = {
            'token': bot_token,
            'channel': channel_id,
            'as_user': 'false',
            'text': text
        }

        bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)

        payload = {
            'time': new_time,
            'response': response,
            'channel': channel_id,
            'channel_name': channel_name,
            'user_id': user_id,
            'bot_token': bot_token
        }
        response = conf.aws_sns.publish(
            TopicArn=conf.aws_sns_timer_arn,
            Message=json.dumps({'default': json.dumps(payload)}),
            MessageStructure='json'
        )
        print 'sns response: %s' % response
        return response


def complete_poll_event(response, message_ts, channel_id, channel_name, bot_token, user_id):
    # poll 메시지 업데이트. 버튼들 제거.
    attachments = response['message']['attachments']
    update_attachments = list()
    for attachment in attachments:
        if 'actions' not in attachment:
            update_attachments.append(attachment)

    update_attachments = json.dumps(update_attachments)
    payload = {
        'token': bot_token,
        'ts': message_ts,
        'channel': response['channel'],
        'text': response['message']['text'],
        'attachments': update_attachments
    }
    bopbot_util.send_request_to_slack(url='https://slack.com/api/chat.update', parameter=payload)

    button_actions = attachments[len(attachments) - 1]['actions']

    result = get_decision_from_button_list(message_ts, button_actions)

    decision_list = result['Decision']
    vote_result_attachments = result['Attachments']
    user_id_list = result['Users']

    vote_result_attachments = json.dumps(vote_result_attachments)

    payload = {"token": str(bot_token), "channel": channel_id, "as_user": "false", 'text': 'Result', 'attachments': vote_result_attachments}
    print bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)

    # joke
    if len(user_id_list) == 0:
        phrase = bopbot_util.get_phrase('poll_joke')

        payload = {"token": str(bot_token), "channel": channel_id, "as_user": "false", 'text': phrase}
        print bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)

    else:
        index = randint(0, len(decision_list)-1)
        decision = decision_list[index]
        location = decision['Location']
        yelp_id = decision['Yelp_id']
        name = '*' + decision['Name'] + '*'

        if len(decision_list) > 1:
            phrase = bopbot_util.get_phrase('poll_tied')
            text = phrase % (len(decision_list), name)
        else:
            phrase = bopbot_util.get_phrase('poll_result')
            text = phrase % name
        print text

        restaurant_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)

        item = restaurant_table.get_item(Key={'Location': location, 'Yelp_id': yelp_id})['Item']

        channel_table = BopBotDatabase(table=conf.CHANNEL_POLL_TABLE)
        channel_table.update_item_to_table(key={'Channel_id': channel_id},
                                           attribute_updates={'Location': {'Action': 'PUT', 'Value': item['Location'].encode('utf8')},
                                                              'User_id': {'Action': 'PUT', 'Value': user_id},
                                                              'Yelp_id': {'Action': 'PUT', 'Value': item['Yelp_id'].encode('utf8')},
                                                              'lat': {'Action': 'PUT', 'Value': item['location']['coordinate']['lat']},
                                                              'lng': {'Action': 'PUT', 'Value': item['location']['coordinate']['lng']},
                                                              'Message_ts': {'Action': 'PUT', 'Value': message_ts}
                                                              }
                                  )
        restaurant_attachment = bopbot_util.make_restaurant_list_attachments([item])
        restaurant_attachment = json.dumps(restaurant_attachment)

        payload = {'token': bot_token, 'channel': channel_id, 'as_user': 'false', 'text': text, 'attachments': restaurant_attachment}
        print bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)

        phrase = bopbot_util.get_phrase('reminder_1')
        text = phrase % name
        payload = {"token": bot_token, "channel": user_id, "as_user": "true", 'text': text}

        reminder_param = {'channel': channel_id, 'channel_name': channel_name, 'decision': name}
        reminder_param = json.dumps(reminder_param)

        actions = []
        for button in bopbot_util.interactive_buttons['reminder_menu']:
            action = bopbot_util.make_im_button(name=button, text=button, value=reminder_param)
            actions.append(action)

        reminder_attachments = [bopbot_util.make_im_button_attachment(callback_id='reminder_menu', actions=actions)]
        reminder_attachments = json.dumps(reminder_attachments)
        payload.update({'attachments': reminder_attachments})
        bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)

    return response


# return {"Decision": decision_list, "Attachments": vote_result_attachments, "Users": user_id_list}
def get_decision_from_button_list(message_ts, button_list):
    vote_table = conf.aws_dynamo_db.Table(conf.VOTE_TABLE)

    vote_result_attachments = list()
    user_id_list = list()

    decision_list = list()
    decision_count = 0

    for index, action in enumerate(button_list):
        value = action['value']
        value = json.loads(value)
        result = vote_table.query(
            KeyConditionExpression=Key('Message_ts').eq(message_ts),
            FilterExpression=Attr('Meta').eq(value)
        )
        items = result['Items']

        voted_user = str()
        for item in items:
            user_id_list.append(item['User_id'])
            voted_user += '<@%s> ' % item['User_id']

        name = action['name'].encode('utf8')
        yelp_id = value['Yelp_id']
        location = value['Location']

        result_text = '%s vote' % result['Count']
        if result['Count'] > 1:
            result_text += 's'
        result_text += '\n'

        result_text += voted_user

        if decision_count < result['Count']:
            decision_list = list()
            decision_count = result['Count']
            decision_list.append({'Name': name, 'Yelp_id': yelp_id, 'Location': location})

        elif decision_count == result['Count']:
            decision_list.append({'Name': name, 'Yelp_id': yelp_id, 'Location': location})

        attachment = {'title': name, 'text': result_text}
        vote_result_attachments.append(attachment)

    for attachment in vote_result_attachments:
        for decision in decision_list:
            if attachment['title'] == decision['Name']:
                attachment.update({'color': '#3aa3e3'})

    return {'Decision': decision_list, 'Attachments': vote_result_attachments, 'Users': user_id_list}

