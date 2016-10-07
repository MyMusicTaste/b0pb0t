import conf
import json
import bopbot_util
from boto3.dynamodb.conditions import Key


def send_start_demo_message(user_id, bot_token):
    """
    :rtype: object
    :param user_id:
    :param bot_token:
    :return:
    """
    try:
        user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
        user_table.put_item(Item={'User_id': user_id, 'Status': 'tutorial'})
    
        callback_id = 'simple_demo_start'
        button = bopbot_util.interactive_buttons[callback_id][0]
        action = {'name': button, 'text': button, 'type': 'button', 'value': button}
    
        attachments = [
            bopbot_util.make_im_button_attachment(text='#Simple demo',
                                                  callback_id=callback_id,
                                                  actions=[action])
        ]
    
        attachments = json.dumps(attachments)
    
        phrase = bopbot_util.get_phrase('tutorial_1')
    
        payload = bopbot_util.get_dict_for_slack_post_request(
            token=bot_token,
            channel=user_id,
            text=phrase,
            attachments=attachments,
            as_user='true'
        )
    
        return bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)
    except Exception, e:
        print e
        return 


def clicked_simple_demo_start(team_id, user_id, bot_token):
    """
    :param team_id:
    :param user_id:
    :param bot_token:
    :return:
    """
    payload = bopbot_util.get_dict_for_slack_post_request(token=bot_token, channel=user_id, as_user='true')

    team_table = conf.aws_dynamo_db.Table(conf.SLACK_TEAM_TABLE)
    response = team_table.get_item(Key={'Team_id': team_id, 'User_id': user_id})
    item = response['Item']

    if 'Access_token' in item:
        payload.update(make_tutorial_restaurant_list('simple_demo_more_options', 'tutorial_3'))
    else:
        phrase = bopbot_util.get_phrase('tutorial_auth')
        attachments = [
            {
                'title': 'Authorization',
                'title_link': 'https://slack.com/oauth/authorize?scope=bot,channels:write,im:write,im:history,reminders:write&state=%s&client_id=%s' % ('tutorial', conf.CLIENT_ID)
            }
        ]
        attachments = json.dumps(attachments)

        payload.update({'text': phrase, 'attachments': attachments})

    return bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)


def clicked_simple_demo_more_options(user_id, bot_token):
    """
    :param user_id:
    :param bot_token:
    :return:
    """
    payload = bopbot_util.get_dict_for_slack_post_request(
        token=bot_token,
        channel=user_id,
        as_user='true',
    )
    payload.update(make_tutorial_restaurant_list(
        callback_id='simple_demo_send_the_poll',
        phrase_key='tutorial_4',
        is_title=False)
    )

    return bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)


def clicked_simple_demo_send_the_poll(user_id, bot_token):
    """

    :param user_id:
    :param bot_token:
    :return:
    """
    user_table = conf.aws_dynamo_db.Table(conf.USER_STATUS_TABLE)
    user_table.put_item(Item={'User_id': user_id})

    phrase = bopbot_util.get_phrase('tutorial_5')
    payload = bopbot_util.get_dict_for_slack_post_request(
        token=bot_token,
        channel=user_id,
        as_user='true',
        text=phrase
    )
    payload.update({'mrkdwn': 'true'})

    return bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)


def make_tutorial_restaurant_list(callback_id, phrase_key, is_title=True):
    """
    :param restaurant_list:
    :param callback_id:
    :param phrase_key:
    :param is_title:
    :return:
    """
    menu_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)
    response = menu_table.query(
        KeyConditionExpression=Key('Location').eq(conf.TUTORIAL_DEFAULT_RESTAURANT_LOCATION)
    )
    items = response['Items']

    if callback_id == 'simple_demo_more_options':
        restaurant_list = items[0:5]
    else:
        restaurant_list = items[5:len(items)]

    attachments = bopbot_util.make_restaurant_list_attachments(restaurant_list)

    button = bopbot_util.interactive_buttons[callback_id][0]

    phrase = bopbot_util.get_phrase(phrase_key)
    action = {'name': button, 'text': button, 'type': 'button', 'value': button}

    attachments.append(bopbot_util.make_im_button_attachment(text=phrase, callback_id=callback_id, actions=[action]))
    attachments = json.dumps(attachments)

    payload = {
        'attachments': attachments
    }

    if is_title:
        phrase = bopbot_util.get_phrase('tutorial_2')
        payload.update({'text': phrase})

    return payload
