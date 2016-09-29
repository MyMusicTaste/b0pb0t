# -*- coding: utf8 -*-
import json
import urllib
import urllib2
import urlparse
from boto3.dynamodb.conditions import Key, Attr
import time
import re
from random import randint
from multiprocessing.dummy import Pool
import datetime
import yelp_api_scraper
import pytz
from geopy.geocoders import GoogleV3
import conf


VOTE_DURATION = 300
MENU_ITEM_COUNT = 3

buttons = ['Send the poll', 'More options']


def lambda_handler(event, context):
    # TODO implement
    print event

    try:
        record = event['Records'][0]
        topic_arn = record['Sns']['TopicArn']
        message = record['Sns']['Message']
        if type(message) is not dict:
            message = json.loads(message)

    except KeyError, e:
        raise Exception('Bad Request: Key error: %s' % e)
    except Exception, e:
        raise Exception('Bad Request: Exception: %s' % e)

    if topic_arn == conf.aws_sns_im_arn:
        # button event
        im_handler(message)
    elif topic_arn == conf.aws_sns_event_arn:
        # chat event
        chat_event_handler(message)
    else:
        return 'Bad Request: Wrong topic arn: %s' % topic_arn


def get_phrase(key):
    phrases_table = conf.aws_dynamo_db.Table(conf.BOT_PHRASES)
    items = phrases_table.query(KeyConditionExpression=Key('Key').eq(key))['Items']
    if len(items) > 1:
        index = randint(0, len(items)-1)
        return items[index]['Phrase'].encode('utf8')
    else:
        phrase = items[0]['Phrase'].encode('utf8')
    return phrase


def send_request(url, parameter):
    try:
        data = urllib.urlencode(parameter, doseq=True)

        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req).read()
        return response
    except Exception, e:
        print e
        raise Exception('Bad Request: %s' % e)


def send_request_wrapper(args):
    return send_request(*args)


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


def send_authorization_request(channel, bot_token, message_ts):
    phrase = get_phrase('main_auth')

    attachments = [
        {
            'title': 'Authorization',
            'title_link': 'https://slack.com/oauth/authorize?scope=bot,channels:write,im:write,im:history,reminders:write&state=%s&client_id=%s' % (message_ts, conf.CLIENT_ID)
        }
    ]
    attachments = json.dumps(attachments)
    payload = {
        'token': bot_token,
        'channel': channel,
        'as_user': 'true',
        'text': phrase,
        'attachments': attachments
    }
    return send_request(conf.CHAT_POST_MESSAGE, payload)


def im_open(user_id, bot_token):
    url = 'https://slack.com/api/im.open'
    payload = {'token': bot_token, 'user': user_id}
    return send_request(url, payload)


def send_message_with_key(key, bot_token, user_id):
    phrase = get_phrase(key)
    payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase}
    return send_request(conf.CHAT_POST_MESSAGE, payload)


def send_stop_message_with_key(key, bot_token, user_id):
    user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
    user_table.put_item(Item={'User_id': user_id})

    phrase = get_phrase(key)
    payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase}
    return send_request(conf.CHAT_POST_MESSAGE, payload)


def chat_event_handler(message):
    print 'Chat event handler'
    print message

    try:
        team_id = message['team_id']

        event_dict = message['event']

        if 'type' in event_dict and event_dict['type'] == 'team_join':
            # Slack event - team_join
            user_id = event_dict['user']['id']

            team_table = conf.aws_dynamo_db.Table(conf.SLACK_TEAM_TABLE)
            response = team_table.get_item(Key={'Team_id': team_id, 'User_id': 'Team'})
            item = response['Item']
            bot_token = item['Bot_access_token']

            return im_open(user_id, bot_token)

        if 'subtype' in event_dict:
            if event_dict['subtype'] == 'message_changed' or event_dict['subtype'] == 'message_deleted':
                return

        if 'bot_id' in event_dict:
            print 'bot message'
            return

        user_id = event_dict['user']
        channel = event_dict['channel']
        text = event_dict['text']
        text_ts = event_dict['ts']

    except KeyError, e:
        raise Exception('Bad Request: Key error: %s' % e)
    except Exception, e:
        raise Exception('Bad Request: Exception: %s' % e)

    team_table = conf.aws_dynamo_db.Table(conf.SLACK_TEAM_TABLE)
    response = team_table.get_item(Key={'Team_id': team_id, 'User_id': 'Team'})

    item = response['Item']
    bot_token = item['Bot_access_token']
    bot_id = item['Bot_user_id']

    if user_id == bot_id:
        print 'bot message'
        return

    print 'bot_id: %s, author_id: %s' % (bot_id, user_id)

    text = text.replace(" ", "").replace(":", "")
    text = text.lower()

    response = team_table.get_item(Key={'Team_id': team_id, 'User_id': user_id})
    if 'Item' not in response:
        # It is a first message with 'what_to_eat' bot, if there is no user data in database.
        team_table.put_item(Item={'Team_id': team_id, 'User_id': user_id})

        user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
        user_table.put_item(Item={'User_id': user_id, 'Status': 'tutorial'})

        return send_start_demo_message(user_id, bot_token)

    team_user_item = response['Item']

    user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
    response = user_table.get_item(Key={'User_id': user_id})

    if 'Item' not in response:
        user_table.put_item(Item={'User_id': user_id})
        item = {'User_id': user_id}
    else:
        item = response['Item']

    if 'Status' not in item:
        payload = {'token': bot_token, 'channel': channel, 'as_user': 'true'}

        if text == 'whattoeat' or text == 'whattoeat?' or 'bopbot' in text:
            if 'Access_token' not in team_user_item:
                return send_authorization_request(channel, bot_token, text_ts)
            else:
                user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
                # reset user info
                user_table.put_item(Item={'User_id': user_id, 'Status': 'wte_location_input'})
                return send_message_with_key('location_1', bot_token, user_id)

        elif text == 'stop':
            return send_stop_message_with_key('error_1', bot_token, user_id)

        elif text == 'demo':
            return send_start_demo_message(user_id, bot_token)

        else:
            payload.update(get_normal_conversation(text))
            return send_request(conf.CHAT_POST_MESSAGE, payload)

    else:
        # User_id에 status가 있는 경우
        status = item['Status'].lower()

# tutorial
        if status == 'tutorial':
            if text == 'whattoeat' or text == 'whattoeat?' or 'bopbot' in text:
                return start_what_to_eat_flow(team_user_item, channel, bot_token, text_ts, user_id, team_id)
            elif text == 'stop':
                return send_stop_message_with_key('error_4', bot_token, user_id)
            elif text == 'demo':
                return send_message_with_key('error_6', bot_token, user_id)
            else:
                return send_message_with_key('error_7', bot_token, user_id)

# wte_location_input
        elif status == 'wte_location_input':
            print 'What to eat location input'
            if text == 'whattoeat' or text == 'whattoeat?' or 'bopbot' in text:
                return send_message_with_key('error_3', bot_token, user_id)
            elif text == 'stop':
                return send_stop_message_with_key('error_4', bot_token, user_id)
            elif text == 'demo':
                return send_start_demo_message(user_id, bot_token)
            elif text == '마이뮤직테이스트' or text == 'mymusictaste':
                location = 'mymusictastehq'
                restaurant_list = make_random_restaurant_list_with_location(location, user_id)

                if len(restaurant_list) == 0:
                    return send_message_with_key('error_8', bot_token, user_id)

                user_table.update_item(Key={'User_id': user_id}, AttributeUpdates={'Status': {'Action': 'PUT', 'Value': 'wte'}, 'Location': {'Action': 'PUT', 'Value': location}})
                attachments = create_restaurant_list_attachment_dict(restaurant_list, location)
                print attachments
                phrase = get_phrase('location_4') % location
                payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase, 'attachments': attachments}

                return send_request(conf.CHAT_POST_MESSAGE, payload)
            else:
                # yelp api를 사용해서 error가 나면
                suggestions = send_wte_input_result(text)

                if len(suggestions) == 0:
                    return send_message_with_key('error_8', bot_token, user_id)
                elif len(suggestions) == 1:
                    location = suggestions[0].encode('utf8')
                    yelp_api_scraper.fetch_restaurants(location)
                    print 'yelp_api_scraper fetch finish'
                    restaurant_list = make_random_restaurant_list_with_location(location, user_id)

                    if len(restaurant_list) == 0:
                        return send_message_with_key('error_8', bot_token, user_id)

                    user_table.update_item(Key={'User_id': user_id}, AttributeUpdates={'Status': {'Action': 'PUT', 'Value': 'wte'}, 'Location': {'Action': 'PUT', 'Value': location}})

                    attachments = create_restaurant_list_attachment_dict(restaurant_list, location)
                    print attachments
                    phrase = get_phrase('location_4') % location
                    payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase, 'attachments': attachments}
                    return send_request(conf.CHAT_POST_MESSAGE, payload)
                else:
                    # len(suggestions) > 1
                    user_table.put_item(Item={'User_id': user_id, 'Status': 'wte_location_choice', 'Suggestion': suggestions})

                    phrase = get_phrase('location_2')
                    phrase += '\n'
                    for index, location in enumerate(suggestions):
                        phrase += '\n' + '%s. %s' % (index+1, location.encode('utf8'))

                    phrase += '\n\n' + get_phrase('location_3')
                    payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase}
                    return send_request(conf.CHAT_POST_MESSAGE, payload)

# wte_location_choice
        elif status == 'wte_location_choice':
            print 'What to eat location choice'
            if text == 'whattoeat' or text == 'whattoeat?' or 'bopbot' in text:
                return send_message_with_key('error_3', bot_token, user_id)
            elif text == 'stop':
                return send_stop_message_with_key('error_4', bot_token, user_id)
            elif text == 'demo':
                return send_start_demo_message(user_id, bot_token)
            elif text == '마이뮤직테이스트' or text == 'mymusictaste':
                location = 'mymusictastehq'
                restaurant_list = make_random_restaurant_list_with_location(location, user_id)

                if len(restaurant_list) == 0:
                    return send_message_with_key('error_8', bot_token, user_id)

                user_table.update_item(Key={'User_id': user_id}, AttributeUpdates={'Status': {'Action': 'PUT', 'Value': 'wte'}, 'Location': {'Action': 'PUT', 'Value': location}})

                attachments = create_restaurant_list_attachment_dict(restaurant_list, location)
                print attachments
                phrase = get_phrase('location_4') % location
                payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase, 'attachments': attachments}
                return send_request(conf.CHAT_POST_MESSAGE, payload)
            else:
                if text.isdigit():
                    # 메뉴불러오는 스탭
                    index = int(text)

                    response = user_table.get_item(Key={'User_id': user_id})
                    item = response['Item']
                    suggestions = item['Suggestion']
                    if index > len(suggestions):
                        return send_message_with_key('error_9', bot_token, user_id)
                    else:
                        location = suggestions[index-1]

                        yelp_api_scraper.fetch_restaurants(location)
                        print 'yelp_api_scraper fetch finish'
                        restaurant_list = make_random_restaurant_list_with_location(location, user_id)

                        if len(restaurant_list) == 0:
                            return send_message_with_key('error_8', bot_token, user_id)

                        user_table.update_item(Key={'User_id': user_id}, AttributeUpdates={'Status': {'Action': 'PUT', 'Value': 'wte'}, 'Location': {'Action': 'PUT', 'Value': location}})

                        attachments = create_restaurant_list_attachment_dict(restaurant_list, location)
                        print attachments
                        phrase = get_phrase('location_4') % location
                        payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase, 'attachments': attachments}
                        return send_request(conf.CHAT_POST_MESSAGE, payload)

                else:
                    # yelp에서 text검사
                    suggestions = send_wte_input_result(text)
                    if len(suggestions) == 0:
                        return send_message_with_key('error_8', bot_token, user_id)
                    elif len(suggestions) == 1:
                        location = suggestions[0]

                        yelp_api_scraper.fetch_restaurants(location)
                        restaurant_list = make_random_restaurant_list_with_location(location, user_id)

                        if len(restaurant_list) == 0:
                            return send_message_with_key('error_8', bot_token, user_id)

                        user_table.update_item(Key={'User_id': user_id}, AttributeUpdates={'Status': {'Action': 'PUT', 'Value': 'wte'}, 'Location': {'Action': 'PUT', 'Value': location}})

                        attachments = create_restaurant_list_attachment_dict(restaurant_list, location)
                        phrase = get_phrase('location_4') % location
                        payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase, 'attachments': attachments}
                        return send_request(conf.CHAT_POST_MESSAGE, payload)
                    else:
                        # len(suggestions) > 1
                        user_table.put_item(Item={'User_id': user_id, 'Status': 'wte_location_choice', 'Suggestion': suggestions})

                        phrase = get_phrase('location_2')
                        phrase += '\n'
                        for index, location in enumerate(suggestions):
                            phrase += '\n' + '%s. %s' % (index+1, location)

                        phrase += '\n\n' + get_phrase('location_3')
                        payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase}
                        return send_request(conf.CHAT_POST_MESSAGE, payload)

# poll
        elif status == 'poll':
            if text == 'whattoeat' or text == 'whattoeat?' or 'bopbot' in text:
                return start_what_to_eat_flow(team_user_item, channel, bot_token, text_ts, user_id, team_id)
                # return send_message_with_key('error_2', bot_token, user_id)
            elif text == 'stop':
                return send_message_with_key('error_5', bot_token, user_id)
            elif text == 'demo':
                # return send_start_demo_message(user_id, bot_token)
                return send_message_with_key('error_2', bot_token, user_id)
            else:
                return send_message_with_key('error_1', bot_token, user_id)

# wte
        elif status == 'wte':
            if text == 'whattoeat' or text == 'whattoeat?' or 'bopbot' in text:
                return send_message_with_key('error_3', bot_token, user_id)
            elif text == 'stop':
                return send_stop_message_with_key('error_4', bot_token, user_id)
            elif text == 'demo':
                return send_start_demo_message(user_id, bot_token)
            else:
                return send_message_with_key('error_9', bot_token, user_id)

# wte_invitation
        elif status == 'wte_invitation':
            if text == 'whattoeat' or text == 'whattoeat?' or 'bopbot' in text:
                return send_message_with_key('error_3', bot_token, user_id)
            elif text == 'stop':
                return send_stop_message_with_key('error_4', bot_token, user_id)
            elif text == 'demo':
                return send_start_demo_message(user_id, bot_token)
            else:
                user_list = re.findall('(<@)(\w+)(>)', text)
                if len(user_list) == 0:
                    phrase = get_phrase('invite_invalid_input')
                    payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase}
                    return send_request(conf.CHAT_POST_MESSAGE, payload)
                else:
                    # 새로운 채널을 만들고 유저들을 초대
                    team_table = conf.aws_dynamo_db.Table(conf.SLACK_TEAM_TABLE)
                    response = team_table.get_item(Key={'Team_id': team_id, 'User_id': user_id})
                    item = response['Item']
                    if 'Access_token' not in item:
                        send_authorization_request(channel, bot_token, text_ts)
                    else:
                        access_token = item['Access_token']
                        response = send_create_channel_request(access_token)

                        channel_id = response['channel']['id']
                        channel_name = response['channel']['name']

                        invite_members_and_post_generate_message(access_token, bot_token, channel_id, channel_name, user_list)

                        response = send_poll_message_request(user_id, bot_token, channel_id)
                        print response
                        # user_table.update_item(Key={'User_id': user_id}, AttributeUpdates={'Status': {'Action': 'PUT', 'Value': 'poll'}})
                        user_table.put_item(Item={'User_id': user_id, 'Status': 'poll'})
                        response = json.dumps(response)

                        payload = {
                            'time': VOTE_DURATION,
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

# reminder
        elif status == 'reminder':
            if text == 'whattoeat' or text == 'whattoeat?' or 'bopbot' in text:
                return start_what_to_eat_flow(team_user_item, channel, bot_token, text_ts, user_id, team_id)
            elif text == 'stop':
                return send_stop_message_with_key('reminder_stop', bot_token, user_id)
            elif text == 'demo':
                return send_start_demo_message(user_id, bot_token)
            else:
                if 'Channel_id' in item:
                    channel_id = item['Channel_id']
                    # decision = item['Decision'].encode('utf8')
                    access_token = team_user_item['Access_token']
                    return send_reminder_process(access_token, bot_token, channel_id, user_id, text)

        else:
            return


def send_wte_input_result(text):
    url = 'https://www.yelp.com/location_suggest/json?prefix=%s' % text

    suggestions = list()
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req).read()
        response = json.loads(response)

        for suggestion in response['suggestions']:
            suggestions.append(suggestion['name'].encode('utf8'))

        return suggestions

    except Exception, e:
        return suggestions


def start_what_to_eat_flow(team_user_item, channel, bot_token, text_ts, user_id, team_id):
    if 'Access_token' not in team_user_item:
        return send_authorization_request(channel, bot_token, text_ts)

    else:
        user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
        # reset user info

        user_table.put_item(Item={'User_id': user_id, 'Status': 'wte_location_input'})
        return send_message_with_key('location_1', bot_token, user_id)

        # user_table.put_item(Item={'User_id': user_id, 'Status': 'wte'})
        #
        # # random menu list 5개와 기본 버튼을 만들어 리턴
        # message_dict = make_random_menu_list(team_id, user_id)
        # payload = {'token': bot_token, 'channel': channel, 'as_user': 'true'}
        # payload.update(message_dict)
        # return  send_request(CHAT_POST_MESSAGE, payload)


def send_reminder_process(access_token, bot_token, channel, user_id, text):
    try:
        channel_table = conf.aws_dynamo_db.Table(conf.CHANNEL_POLL_TABLE)
        response = channel_table.get_item(Key={'Channel_id': channel})
        item = response['Item']

        location = item['Location']
        yelp_id = item['Yelp_id']
        restaurant_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)
        response = restaurant_table.get_item(Key={'Location': location, 'Yelp_id': yelp_id})
        yelp_item = response['Item']
        decision = yelp_item['name'].encode('utf8')

        lat = yelp_item['location']['coordinate']['lat']
        lng = yelp_item['location']['coordinate']['lng']

    except Exception, e:
        print 'send_reminder_process: %s' % e
        return

    # payload = {'token': bot_token, 'channel': channel}
    # response = send_request('https://slack.com/api/channels.info', payload)
    # response = json.loads(response)
    # members = response['channel']['members']

    members = list()
    vote_table = conf.aws_dynamo_db.Table(conf.VOTE_TABLE)
    response = vote_table.query(
        KeyConditionExpression=Key('Message_ts').eq(item['Message_ts'])
    )
    items = response['Items']
    for item in items:
        members.append(item['User_id'])

    url = 'https://slack.com/api/reminders.add'
    phrase = get_phrase('reminder_text')
    payload = {'token': access_token, 'time': text, 'user': user_id, 'text': phrase % decision}
    response = send_request(url, payload)
    response = json.loads(response)

    if response['ok']:
        timestamp = response['reminder']['time']

        try:
            utc = pytz.utc
            date = datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=utc)

            google = GoogleV3()
            google.timeout = 60
            timezone = google.timezone('%s, %s' % (lat, lng))
            date = timezone.normalize(date.astimezone(timezone))
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        except Exception, e:
            print e
            date = datetime.datetime.fromtimestamp(timestamp)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
            date += ' UTC'

        remind_params = list()
        for member in members:
            if member == user_id:
                continue

            payload = {'token': access_token, 'time': text, 'user': member, 'text': phrase % decision}
            param = (url, payload)
            remind_params.append(param)

        pool = Pool(4)
        results = pool.map(send_request_wrapper, remind_params)
        print 'Reminder pool results: %s' % results

        phrase = get_phrase('reminder_added')
        payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase % date}
        send_request(conf.CHAT_POST_MESSAGE, payload)

        user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
        user_table.put_item(Item={'User_id': user_id})

        phrase = get_phrase('reminder_archive') % channel
        archive_attachments = [
            {
                'color': '#3aa3e3',
                'attachment_type': 'default',
                'fallback': 'archive_channel',
                'callback_id': 'archive_channel',
                'actions': [
                    {
                        'name': 'Archive',
                        'text': 'Archive',
                        'type': 'button',
                        'value': channel
                    },
                    {
                        'name': 'Later',
                        'text': 'Later',
                        'type': 'button',
                        'value': channel
                    }
                ]
            }
        ]
        archive_attachments = json.dumps(archive_attachments)

        payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase, 'attachments': archive_attachments}
        response = send_request(conf.CHAT_POST_MESSAGE, payload)
        print 'archive result: %s' % response
        return response

    else:
        phrase = get_phrase('reminder_add_invalid_input')
        payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase}
        response = send_request(conf.CHAT_POST_MESSAGE, payload)
        print 'Reminder typing: Invalid input %s' % response
        return response


def make_random_restaurant_list_with_location(location, user_id):
    restaurant_list = list()
    try:
        restaurant_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)
        response = restaurant_table.query(
            KeyConditionExpression=Key('Location').eq(location)
        )
        items = response['Items']
        print response

        while len(restaurant_list) < 5:
            index = randint(0, len(items)-1)
            item = items[index]

            restaurant = {'Location': item['Location'], 'Yelp_id': item['Yelp_id'], 'name': item['name'], 'image_url': item['image_url'], 'categories': item['categories'], 'url': item['url']}
            restaurant_list.append(restaurant)
            items.remove(item)
        print restaurant_list
        user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
        user_table.update_item(Key={'User_id': user_id}, AttributeUpdates={'Current_list': {'Action': 'PUT', 'Value': restaurant_list}})
        return restaurant_list
    except Exception, e:
        return restaurant_list


def create_restaurant_list_attachment_dict(restaurants, location):
    restaurant_list = list()
    print
    for restaurant in restaurants:
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
        restaurant_list.append(attachment)

    restaurant_list.append(create_button_menu_with_location(location))

    restaurant_list = json.dumps(restaurant_list)
    return restaurant_list


# Create 'Send the poll' and 'More options' button
# return button attachments dictionary
def create_button_menu_with_location(location):
    actions = list()
    for index, name in enumerate(buttons):
        action = {
            'name': name,
            'text': name,
            'type': 'button',
            'value': location
        }
        actions.append(action)

    button_attachment = {
        'color': '#3aa3e3',
        'attachment_type': 'default',
        'fallback': "default menu",
        'callback_id': "menu_event",
        'actions': actions
    }
    return button_attachment


# return {'text': text, 'attachments': attachments}
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


# Create the channel for poll
def send_create_channel_request(access_token):
    ts = time.time()
    url = 'https://slack.com/api/channels.create'
    phrase = get_phrase('channel_create')
    payload = {'token': access_token, 'name': phrase % ts}
    response = send_request(url=url, parameter=payload)
    print 'channel create request response'
    print response

    if type(response) == str:
        response = json.loads(response)
    return response


# Invite members to channel and send channel generate message
def invite_members_and_post_generate_message(access_token, bot_token, channel_id, channel_name, user_list):
    invite_params = list()
    dm_params = list()
    url = 'https://slack.com/api/channels.invite'
    for index, user in enumerate(user_list):
        payload = {'token': access_token, 'user': user[1].upper(), 'channel': channel_id.upper()}
        param = (url, payload)
        print param
        invite_params.append(param)

        phrase = get_phrase('poll_channel_generated')
        dm_payload = {'token': bot_token, 'channel': user[1].upper(), 'as_user': 'true', 'text': phrase % channel_id}
        dm_param = (conf.CHAT_POST_MESSAGE, dm_payload)
        print dm_param
        dm_params.append(dm_param)

    pool = Pool(4)
    results = pool.map(send_request_wrapper, invite_params)
    print 'Invite Pool result'
    print results
    results = pool.map(send_request_wrapper, dm_params)
    print 'DM Pool result'
    print results


# Post poll message
def send_poll_message_request(user_id, bot_token, channel):
    # access_token으로 채널을 만들고 유저들을 invite시키고 dm으로 채널명 전송.
    #  {'text': '채널 생성 및 초대 성공'}
    user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)

    response = user_table.get_item(Key={'User_id': user_id})
    if 'Current_list' not in response['Item']:
        return

    current_items = response['Item']['Current_list']

    channel_table = conf.aws_dynamo_db.Table(conf.CHANNEL_POLL_TABLE)
    channel_table.put_item(Item={'Channel_id': channel, 'List': current_items})

    attachments = list()

    button_actions = list()
    for item in current_items:
        value = {'Location': item['Location'].encode('utf8'), 'Yelp_id': item['Yelp_id'].encode('utf8')}
        value = json.dumps(value)

        categories = item['categories']
        categories_text = str()
        for index, category in enumerate(categories):
            if index < 3:
                if index == 0:
                    categories_text += category['name'].encode('utf8')
                else:
                    categories_text += ', ' + category['name'].encode('utf8')

        attachment = {
            'title': item['name'].encode('utf8'),
            'title_link': item['url'].encode('utf8'),
            'text': categories_text,
            'thumb_url': item['image_url'].encode('utf8'),
            'color': '#3aa3e3'
        }
        attachments.append(attachment)

        action = {
            'name': item['name'].encode('utf8'),
            'text': item['name'].encode('utf8'),
            'type': 'button',
            'value': value
        }
        button_actions.append(action)

    phrase = get_phrase('poll_vote')
    button_attachment = {
        'color': '#3aa3e3',
        'attachment_type': 'default',
        'fallback': "default menu",
        'callback_id': "menu_event_general",
        'actions': button_actions
    }
    attachments.append(button_attachment)

    attachments = json.dumps(attachments)

    message_dict = {
        'text': phrase,
        'attachments': attachments
    }

    payload = {'token': bot_token, 'channel': channel, 'as_user': 'false'}
    payload.update(message_dict)
    response = send_request(conf.CHAT_POST_MESSAGE, payload)

    if type(response) == str:
        response = json.loads(response)

    print response
    return response


def get_normal_conversation(text):
    if text == 'hi' or text == 'hello':
        hi_message = [
            'Hi~!',
            'Yo!'
        ]
        return {
            'text': hi_message[randint(0, len(hi_message)-1)]
        }
    else:

        text = get_phrase('error_1')
        return {'text': text}


def im_handler(message):
    print 'IM handler'

    try:
        body_dict = message['body-json']

        payload = str(urllib.unwrap(body_dict))
        # payload = str(urllib.unquote(payload).decode('utf8'))
        payload = urlparse.parse_qs(payload)

        payload_dict = payload['payload'][0]

        json_dict = json.loads(payload_dict)

        actions = json_dict['actions']

        menu_name = str(actions[0]['name'])

        channel = json_dict['channel']['id']
        team_id = json_dict['team']['id']
        user_id = json_dict['user']['id']

    except KeyError, e:
        raise Exception('Bad Request: %s' % e)
    except Exception, e:
        raise Exception('Bad Request: %s' % e)

    team_table = conf.aws_dynamo_db.Table(conf.SLACK_TEAM_TABLE)
    response = team_table.get_item(Key={'Team_id': team_id, 'User_id': 'Team'})

    try:
        item = response['Item']
        bot_token = item['Bot_access_token']

        callback = json_dict['callback_id']
    except KeyError, e:
        raise Exception('Bad Request: %s' % e)
    except Exception, e:
        raise Exception('Bad Request: %s' % e)

    if callback == 'menu_event':
        if menu_name == buttons[0]:
            # dm에 who do you wnat.... type the user name을 출력
            # user status를 invitation으로 바꾼다
            user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
            user_table.get_item(Key={'User_id': user_id})
            return click_send_the_poll_button(json_dict, bot_token)
        elif menu_name == buttons[1]:
            location = actions[0]['value']
            restaurant_list = make_random_restaurant_list_with_location(location, user_id)
            attachments = create_restaurant_list_attachment_dict(restaurant_list, location)
            phrase = get_phrase('location_4') % location
            payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase, 'attachments': attachments}
            return send_request(url=conf.CHAT_POST_MESSAGE, parameter=payload)
        else:
            return

    elif callback == 'archive_channel':
        if menu_name == 'Archive':
            channel_id = str(actions[0]['value'])

            response = team_table.get_item(Key={'Team_id': team_id, 'User_id': user_id})
            item = response['Item']
            access_token = item['Access_token']

            # channel archive
            url = 'https://slack.com/api/channels.archive'
            payload = {'token': access_token, 'channel': channel_id}
            response = send_request(url, payload)
            print 'Archive request: %s' % response
            return response
        elif menu_name == 'Later':
            return

    elif callback == 'simple_demo_start':
        response = team_table.get_item(Key={'Team_id': team_id, 'User_id': user_id})

        item = response['Item']

        if 'Access_token' in item:
            payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true'}
            payload.update(make_tutorial_more_option_list())
            return send_request(conf.CHAT_POST_MESSAGE, payload)
        else:
            return

    elif callback == 'simple_demo_more_options':
        payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true'}
        payload.update(click_tutorial_more_option_button())
        return send_request(conf.CHAT_POST_MESSAGE, payload)

    elif callback == 'reminder_menu':
        reminder_param = str(actions[0]['value'])
        reminder_param = json.loads(reminder_param)

        channel_id = reminder_param['channel']

        user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
        if menu_name == 'Set reminder':
            user_table.put_item(Item={'User_id': user_id, 'Channel_id': channel_id, 'Status': 'reminder'})

            phrase = get_phrase('reminder_add')
            payload = {'token': bot_token, 'channel': channel, 'as_user': 'true', 'text': phrase}
            response = send_request(conf.CHAT_POST_MESSAGE, payload)
            print 'reminder response %s' % response
            return response
        elif menu_name == 'No thanks':
            user_table.put_item(Item={'User_id': user_id})

            phrase = get_phrase('reminder_archive') % channel_id
            archive_attachments = [
                {
                    'color': '#3aa3e3',
                    'attachment_type': 'default',
                    'fallback': 'archive_channel',
                    'callback_id': 'archive_channel',
                    'actions': [
                        {
                            'name': 'Archive',
                            'text': 'Archive',
                            'type': 'button',
                            'value': channel_id
                        },
                        {
                            'name': 'Later',
                            'text': 'Later',
                            'type': 'button',
                            'value': channel_id
                        }
                    ]
                }
            ]
            archive_attachments = json.dumps(archive_attachments)

            payload = {'token': bot_token, 'channel': channel, 'as_user': 'true', 'text': phrase, 'attachments': archive_attachments}
            return send_request(conf.CHAT_POST_MESSAGE, payload)

    else:
        return


def click_tutorial_more_option_button():
    menu_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)
    response = menu_table.query(
        KeyConditionExpression=Key('Location').eq(conf.TUTORIAL_DEFAULT_RESTAURANT_LOCATION)
    )
    items = response['Items']

    attachments = list()
    for index, restaurant in enumerate(items[5:len(items)]):
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

    phrase = get_phrase('tutorial_4')

    attachments.append(
        {
            'text': phrase,
            'color': '#3aa3e3',
            'attachment_type': 'default',
            'fallback': "simple_demo_send_the_poll",
            'callback_id': "simple_demo_send_the_poll",
            'actions': [
                {
                    'name': 'Send the poll',
                    'text': 'Send the poll',
                    'type': 'button',
                    'value': 'Send the poll'
                }
            ]
        }
    )

    attachments = json.dumps(attachments)

    message_dict = {
        'text': 'Thanks! Let\'s see how it works!',
        'attachments': attachments
    }

    return message_dict


def click_send_the_poll_button(json_dict, bot_token):
    channel = json_dict['channel']['id']
    user_id = json_dict['user']['id']

    phrase = get_phrase('invite')
    message_dict = {'text': phrase}

    user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)

    response = user_table.get_item(Key={'User_id': user_id})
    item = response['Item']
    if 'Current_list' not in item:
        return

    user_table.update_item(Key={'User_id': user_id}, AttributeUpdates={'Status': {'Action': 'PUT', 'Value': 'wte_invitation'}})

    payload = {'token': bot_token, 'channel': channel, 'as_user': 'true'}
    payload.update(message_dict)

    return send_request(conf.CHAT_POST_MESSAGE, payload)
