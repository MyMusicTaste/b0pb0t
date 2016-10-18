# -*- coding: utf8 -*-
import conf
import bopbot_util
import bopbot_tutorial
import json
import yelp_api_scraper
from random import randint
from database_manager import BopBotDatabase
from boto3.dynamodb.conditions import Key
import re
import time
import pytz
from geopy.geocoders import GoogleV3
import datetime
import sys
import event_chat_message


def send_authorization_request(channel, bot_token):
    phrase = bopbot_util.get_phrase('main_auth')

    attachments = [
        {
            'title': 'Authorization',
            'title_link': 'https://slack.com/oauth/authorize?scope=bot,channels:write,im:write,im:history,reminders:write&client_id=%s' % conf.CLIENT_ID
        }
    ]
    attachments = json.dumps(attachments)

    payload = bopbot_util.get_dict_for_slack_post_request(
        token=bot_token,
        channel=channel,
        text=phrase,
        attachments=attachments
    )

    return bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)


def send_stop_message_with_key(key, bot_token, user_id):
    item = {'User_id': user_id}
    user_table.put_item_to_table(item=item)

    return send_simple_message_to_slack_with_key(
        key=key,
        bot_token=bot_token,
        user_id=user_id
    )


def send_simple_message_to_slack_with_key(key, bot_token, user_id):
    phrase = bopbot_util.get_phrase(key)
    payload = bopbot_util.get_dict_for_slack_post_request(
        token=bot_token,
        channel=user_id,
        text=phrase
    )
    return bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)


def team_join_event_handler(team_id, user_id):
    key = {'Team_id': team_id, 'User_id': 'Team'}
    item = team_table.get_item_from_table(key=key)
    bot_token = item['Bot_access_token']

    return bopbot_util.im_open(user_id, bot_token)


def start_what_to_eat_flow(bot_token, user_id, access_token=False):
    if not access_token:
        return send_authorization_request(channel=user_id, bot_token=bot_token)
    else:
        item = {'User_id': user_id, 'Status': 'wte_location_input'}
        user_table.put_item_to_table(item=item)
        return send_simple_message_to_slack_with_key(
            key='location_1',
            bot_token=bot_token,
            user_id=user_id
        )


def chat_event_handler(message):
    print 'Chat event handler'

    try:
        team_id = message['team_id']
        event_dict = message['event']

        if 'type' in event_dict and event_dict['type'] == 'team_join':
            # slack event - team_join
            user_id = event_dict['user']['id']
            return team_join_event_handler(team_id, user_id)

        if 'subtype' in event_dict:
            # it's not a user command.
            if event_dict['subtype'] == 'message_changed' or event_dict['subtype'] == 'message_deleted':
                return

        if 'bot_id' in event_dict:
            # ignore bot users command.
            print 'bot message'
            return

        user_id = event_dict['user']
        user_command = event_dict['text']

    except KeyError, e:
        raise Exception('Bad Request: Key error: %s' % e)
    except Exception, e:
        raise Exception('Bad Request: Exception: %s' % e)

    global team_table
    global user_table
    global restaurant_table

    team_table = BopBotDatabase(table=conf.SLACK_TEAM_TABLE)
    user_table = BopBotDatabase(table=conf.USER_STATUS_TABLE)
    restaurant_table = BopBotDatabase(table=conf.RESTAURANT_TABLE)

    key = {'Team_id': team_id, 'User_id': 'Team'}
    item = team_table.get_item_from_table(key=key)

    bot_token = item['Bot_access_token']
    bot_id = item['Bot_user_id']

    if user_id == bot_id:
        print 'bot message'
        return

    user_command = user_command.replace(" ", "").replace(":", "")
    user_command = user_command.lower()

    key = {'Team_id': team_id, 'User_id': user_id}
    item = team_table.get_item_from_table(key=key)
    if not item:
        # start demo flow, if there is no user data in SlackTeamBot table.
        item = {'Team_id': team_id, 'User_id': user_id}
        team_table.put_item_to_table(item=item)
        return bopbot_tutorial.send_start_demo_message(user_id, bot_token)
    else:
        if 'Access_token' in item:
            access_token = item['Access_token']
        else:
            access_token = False

    key = {'User_id': user_id}
    item = user_table.get_item_from_table(key=key)
    if not item:
        user_table.put_item_to_table(item={'User_id': user_id})
        item = {"User_id": user_id}

    if 'Status' not in item:
        status = 'normal'
    else:
        # User_id에 status가 있는 경우
        status = item['Status']

    return handler_user_command_with_status(status=status, user_command=user_command, bot_token=bot_token, user_id=user_id, access_token=access_token)


def handler_user_command_with_status(status, user_command, bot_token, user_id, access_token):
    command_table = BopBotDatabase(conf.COMMAND_TABLE)

    item = command_table.get_item_from_table(key={'Status': 'wte_commands'})
    if not item:
        print 'item does not exists'
        return

    wte_commands = item['Commands']

    item = command_table.get_item_from_table(key={'Status': status})

    if not item:
        print 'item does not exists'
        return

    command_def = item['Command_def']

    # 유저의 명령어가 wte command list에 있는지 검사.
    if len(filter(lambda x: x in user_command, wte_commands)) > 0:
        # what to eat command
        user_command = 'wte'

    if user_command in command_def:
        item = command_def[user_command]
    else:
        item = item['Else']

    module = item['module']
    if len(module) == 0:
        module = 'event_chat_message'
    module = getattr(sys.modules[__name__], module)

    function = item['function']
    function = getattr(module, function)

    parameters = item['parameters']
    kwargs = {}
    for param in parameters:
        if '=' in param:
            params = param.split('=')
            kwargs[params[0]] = params[1]
        else:
            kwargs[param] = locals()[param]

    return function(**kwargs)


def send_wte_input_to_yelp(input):
    url = 'https://www.yelp.com/location_suggest/json?prefix=%s' % input

    suggestions = list()
    try:
        response = bopbot_util.send_request(url=url)
        if response:
            yelp_result = json.loads(response)
            for suggestion in yelp_result['suggestions']:
                suggestions.append(suggestion['name'].encode('utf8'))

        return suggestions

    except Exception, e:
        print e
        return suggestions


def process_wte_location_input(bot_token, user_id, user_command):
    # yelp api를 사용해서 error가 나면
    suggestions = send_wte_input_to_yelp(user_command)

    if len(suggestions) == 0:
        return send_simple_message_to_slack_with_key(key='error_8', bot_token=bot_token, user_id=user_id)
    elif len(suggestions) == 1:
        # location = suggestions[0].encode('utf8')
        location = suggestions[0]
        return send_random_restaurant_list(location=location, bot_token=bot_token, user_id=user_id, is_yelp=True)
    else:
        # len(suggestions) > 1
        item = {'User_id': user_id, 'Status': 'wte_location_choice', 'Suggestion': suggestions}
        user_table.put_item_to_table(item=item)

        phrase = bopbot_util.get_phrase('location_2')
        phrase += '\n'
        for index, location in enumerate(suggestions):
            phrase += '\n' + '%s. %s' % (index+1, location)

        phrase += '\n\n' + bopbot_util.get_phrase('location_3')
        payload = bopbot_util.get_dict_for_slack_post_request(token=bot_token, channel=user_id, text=phrase)
        return bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)


def process_wte_location_choice(bot_token, user_id, user_command):
    try:
        index = int(user_command)
        item = user_table.get_item_from_table(key={'User_id': user_id})
        suggestions = item['Suggestion']

        if index > len(suggestions) or index <= 0:
            return send_simple_message_to_slack_with_key(key='error_9', bot_token=bot_token, user_id=user_id)
        else:
            location = suggestions[index-1]
            return send_random_restaurant_list(location=location, bot_token=bot_token, user_id=user_id, is_yelp=True)

    except ValueError, e:
        return process_wte_location_input(bot_token=bot_token, user_id=user_id, user_command=user_command)


def send_random_restaurant_list(location, bot_token, user_id, is_yelp=False):
    if is_yelp:
        yelp_api_scraper.fetch_restaurants(location)
        print 'yelp_api_scraper fetch finish'

    restaurant_list = make_random_restaurant_list_with_location(location)

    if len(restaurant_list) == 0:
        return send_simple_message_to_slack_with_key(key='error_8', bot_token=bot_token, user_id=user_id)

    user_table.update_item_to_table(key={'User_id': user_id}, attribute_updates={'Status': {'Action': 'PUT', 'Value': 'wte'},
                                                                                 'Location': {'Action': 'PUT', 'Value': location},
                                                                                 'Current_list': {'Action': 'PUT', 'Value': restaurant_list}})

    attachments = bopbot_util.make_restaurant_list_attachments(restaurant_list)

    actions = []
    for button in bopbot_util.interactive_buttons['menu_event']:
        action = bopbot_util.make_im_button(name=button, text=button, value=location)
        actions.append(action)

    im_attachment = bopbot_util.make_im_button_attachment(callback_id='menu_event', actions=actions)
    attachments.append(im_attachment)
    print attachments

    attachments = json.dumps(attachments)

    phrase = bopbot_util.get_phrase('location_4') % location
    payload = bopbot_util.get_dict_for_slack_post_request(token=bot_token, channel=user_id, text=phrase, attachments=attachments)
    return bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)


def make_random_restaurant_list_with_location(location):
    """
    make restaurant list randomly
    :param location: query key
    :param user_id:
    :return:
    """
    restaurant_list = list()
    try:
        query = Key('Location').eq(location)

        items = restaurant_table.query_items_from_table(query)

        if len(items) < 5:
            count_range = range(0, len(items))
        else:
            count_range = range(0, 5)

        for i in count_range:
            index = randint(0, len(items)-1)
            item = items[index]

            restaurant = {'Location': item['Location'], 'Yelp_id': item['Yelp_id'], 'name': item['name'], 'image_url': item['image_url'], 'categories': item['categories'], 'url': item['url']}
            restaurant_list.append(restaurant)
            items.remove(item)
        print restaurant_list

        return restaurant_list
    except Exception, e:
        return restaurant_list


# process wte_invitation flow
def process_wte_invitation(bot_token, user_id, user_command, access_token):
    user_list = re.findall('(<@)(\w+)(>)', user_command)
    if len(user_list) == 0:
        phrase = bopbot_util.get_phrase('invite_invalid_input')
        payload = {'token': bot_token, 'channel': user_id, 'as_user': 'true', 'text': phrase}
        return bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)
    else:
        # 새로운 채널을 만들고 유저들을 초대
        if not access_token:
            return send_authorization_request(channel=user_id, bot_token=bot_token)
        else:
            print user_list
            response = send_create_channel_request(access_token)

            if not response:
                return

            channel_id = response['channel']['id']
            channel_name = response['channel']['name']

            send_invite_members_to_channel(access_token=access_token, members=user_list, channel_id=channel_id)
            send_channel_generate_message(members=user_list, bot_token=bot_token, channel_id=channel_id)

            response = send_poll_message_request(user_id, bot_token, channel_id)
            print response
            if not response:
                print 'send poll message failed'
                return

            payload = {
                'time': conf.VOTE_DURATION,
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

            item = {'User_id': user_id, 'Status': 'poll'}
            user_table.put_item_to_table(item=item)
            return response


def send_create_channel_request(access_token):
    ts = time.time()
    url = 'https://slack.com/api/channels.create'
    phrase = bopbot_util.get_phrase('channel_create')
    payload = {'token': access_token, 'name': phrase % ts}
    response = bopbot_util.send_request_to_slack(url=url, parameter=payload)
    print 'channel create request response'
    print response

    if type(response) == str:
        response = json.loads(response)
    return response


def send_invite_members_to_channel(access_token, members, channel_id):
    params = []
    for member in members:
        # member = ['<@', 'user id', '>']
        url = 'https://slack.com/api/channels.invite'
        payload = {'token': access_token, 'user': member[1].upper(), 'channel': channel_id}
        param = (url, payload)
        params.append(param)

    results = bopbot_util.send_request_with_multiprocessing_pool(4, params)
    print 'Invite pool result: %s' % results


def send_channel_generate_message(members, bot_token, channel_id):
    params = []
    phrase = bopbot_util.get_phrase('poll_channel_generated')
    for member in members:
        payload = bopbot_util.get_dict_for_slack_post_request(bot_token, member[1].upper(), phrase % channel_id)
        param = (conf.CHAT_POST_MESSAGE, payload)
        params.append(param)

    results = bopbot_util.send_request_with_multiprocessing_pool(4, params)
    print 'DM pool result: %s' % results


def send_poll_message_request(user_id, bot_token, channel):
    # access_token으로 채널을 만들고 유저들을 invite시키고 dm으로 채널명 전송.
    #  {'text': '채널 생성 및 초대 성공'}

    response = user_table.get_item_from_table(key={'User_id': user_id})
    if 'Current_list' not in response:
        return

    current_items = response['Current_list']

    channel_table = BopBotDatabase(table=conf.CHANNEL_POLL_TABLE)
    item = {'Channel_id': channel, 'List': current_items}
    channel_table.put_item_to_table(item=item)

    button_actions = []

    attachments = bopbot_util.make_restaurant_list_attachments(restaurant_list=current_items)

    for item in current_items:
        value = {'Location': item['Location'].encode('utf8'), 'Yelp_id': item['Yelp_id'].encode('utf8')}
        value = json.dumps(value)
        name = item['name'].encode('utf8')
        action = bopbot_util.make_im_button(name=name, text=name, value=value)
        button_actions.append(action)

    button_attachment = bopbot_util.make_im_button_attachment(callback_id='menu_event_general', actions=button_actions)
    attachments.append(button_attachment)
    attachments = json.dumps(attachments)

    phrase = bopbot_util.get_phrase('poll_vote')
    payload = bopbot_util.get_dict_for_slack_post_request(token=bot_token, channel=channel, text=phrase, attachments=attachments, as_user='false')
    return bopbot_util.send_request_to_slack(url=conf.CHAT_POST_MESSAGE, parameter=payload)


def send_reminder_process(bot_token, user_id, user_command, access_token):
    item = user_table.get_item_from_table(key={'User_id': user_id})

    if 'Channel_id' not in item:
        return

    channel_id = item['Channel_id']

    try:
        channel_table = BopBotDatabase(table=conf.CHANNEL_POLL_TABLE)
        item = channel_table.get_item_from_table(key={'Channel_id': channel_id})

        location = item['Location']
        yelp_id = item['Yelp_id']

        yelp_item = restaurant_table.get_item_from_table(key={'Location': location, 'Yelp_id': yelp_id})
        decision = yelp_item['name'].encode('utf8')

        lat = yelp_item['location']['coordinate']['lat']
        lng = yelp_item['location']['coordinate']['lng']

    except Exception, e:
        print 'send_reminder_process: %s' % e
        return

    members = list()
    vote_table = BopBotDatabase(table=conf.VOTE_TABLE)
    items = vote_table.query_items_from_table(query=Key('Message_ts').eq(item['Message_ts']))

    for item in items:
        members.append(item['User_id'])

    url = 'https://slack.com/api/reminders.add'
    phrase = bopbot_util.get_phrase('reminder_text')
    payload = {'token': access_token, 'time': user_command, 'user': user_id, 'text': phrase % decision}
    # response = bopbot_util.send_request(url, payload)
    # response = response['result']

    response = bopbot_util.send_request_to_slack(url=url, parameter=payload)
    # response = json.loads(response)

    if response:
        timestamp = response['reminder']['time']

        try:
            utc = pytz.utc
            date = datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=utc)

            google = GoogleV3()
            google.timeout = 60
            timezone = google.timezone('%s, %s' % (lat, lng))
            print 'timezone: %s' % timezone
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

            payload = {'token': access_token, 'time': user_command, 'user': member, 'text': phrase % decision}
            param = (url, payload)
            remind_params.append(param)

        results = bopbot_util.send_request_with_multiprocessing_pool(4, remind_params)
        print 'Reminder pool results: %s' % results

        phrase = bopbot_util.get_phrase('reminder_added')
        payload = bopbot_util.get_dict_for_slack_post_request(token=bot_token, channel=user_id, text=phrase%date)
        bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)

        user_table.put_item_to_table(item={'User_id': user_id})

        payload = bopbot_util.make_archive_payload(bot_token=bot_token, user_id=user_id, channel=channel_id)
        response = bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)
        print 'archive result: %s' % response
        return response

    else:
        phrase = bopbot_util.get_phrase('reminder_add_invalid_input')
        payload = bopbot_util.get_dict_for_slack_post_request(token=bot_token, channel=user_id, text=phrase)
        response = bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)
        print 'Reminder typing: Invalid input %s' % response
        return response

