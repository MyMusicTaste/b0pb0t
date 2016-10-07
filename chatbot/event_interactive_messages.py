import conf
import bopbot_util
import bopbot_tutorial
import json
from database_manager import BopBotDatabase
import event_chat_message
import urllib
import urlparse


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

    global team_table
    global user_table

    team_table = BopBotDatabase(table=conf.SLACK_TEAM_TABLE)
    user_table = BopBotDatabase(table=conf.USER_STATUS_TABLE)

    try:
        item = team_table.get_item_from_table(key={'Team_id': team_id, 'User_id': 'Team'})
        bot_token = item['Bot_access_token']
        callback = json_dict['callback_id']

    except KeyError, e:
        raise Exception('Bad Request: %s' % e)
    except Exception, e:
        raise Exception('Bad Request: %s' % e)

    if callback == 'menu_event':
        if menu_name == bopbot_util.interactive_buttons[callback][0]:
            # send the poll
            return clicked_send_the_poll_button(bot_token=bot_token, user_id=user_id)
        elif menu_name == bopbot_util.interactive_buttons[callback][1]:
            # more options
            location = actions[0]['value']
            return clicked_more_options_button(bot_token=bot_token, user_id=user_id, location=location)

    elif callback == 'simple_demo_start':
        return bopbot_tutorial.clicked_simple_demo_start(team_id=team_id, user_id=user_id, bot_token=bot_token)

    elif callback == 'simple_demo_more_options':
        return bopbot_tutorial.clicked_simple_demo_more_options(user_id=user_id, bot_token=bot_token)

    elif callback == 'simple_demo_send_the_poll':
        return bopbot_tutorial.clicked_simple_demo_send_the_poll(user_id=user_id, bot_token=bot_token)

    elif callback == 'reminder_menu':
        reminder_param = str(actions[0]['value'])
        reminder_param = json.loads(reminder_param)

        channel_id = reminder_param['channel']

        if menu_name == bopbot_util.interactive_buttons[callback][0]:
            user_table.put_item_to_table(item={'User_id': user_id, 'Channel_id': channel_id, 'Status': 'reminder'})

            phrase = bopbot_util.get_phrase('reminder_add')
            payload = {'token': bot_token, 'channel': channel, 'as_user': 'true', 'text': phrase}
            response = bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)
            print 'reminder response %s' % response
            return response
        elif menu_name == bopbot_util.interactive_buttons[callback][1]:
            user_table.put_item_to_table(item={'User_id': user_id})
            payload = bopbot_util.make_archive_payload(bot_token=bot_token, user_id=user_id, channel=channel_id)
            return bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)

    elif callback == 'archive_channel':
        if menu_name == bopbot_util.interactive_buttons[callback][0]:
            #archive
            channel_id = str(actions[0]['value'])

            item = team_table.get_item_from_table(key={'Team_id': team_id, 'User_id': user_id})
            access_token = item['Access_token']

            # channel archive
            url = 'https://slack.com/api/channels.archive'
            payload = {'token': access_token, 'channel': channel_id}
            response = bopbot_util.send_request(url, payload)
            print 'Archive request: %s' % response
            return response
        elif menu_name == 'Later':
            return

    else:
        return


def clicked_send_the_poll_button(bot_token, user_id):
    phrase = bopbot_util.get_phrase('invite')
    item = user_table.get_item_from_table(key={'User_id': user_id})
    if 'Current_list' not in item:
        return

    user_table.update_item_to_table(key={'User_id': user_id}, attribute_updates={'Status': {'Action': 'PUT', 'Value': 'wte_invitation'}})

    payload = bopbot_util.get_dict_for_slack_post_request(token=bot_token, channel=user_id, text=phrase)
    return bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)


def clicked_more_options_button(bot_token, user_id, location):
    return event_chat_message.send_random_restaurant_list(location=location, bot_token=bot_token, user_id=user_id)