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
    response = json.loads(response)
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
        bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)

        response = json.dumps(response)
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
    bopbot_util.send_request('https://slack.com/api/chat.update', payload)

    button_actions = attachments[len(attachments) - 1]['actions']

    result = get_decision_from_button_list(message_ts, button_actions)

    decision_list = result['Decision']
    vote_result_attachments = result['Attachments']
    user_id_list = result['Users']

    vote_result_attachments = json.dumps(vote_result_attachments)

    payload = {"token": str(bot_token), "channel": channel_id, "as_user": "false", 'text': 'Result', 'attachments': vote_result_attachments}
    print bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)

    # 투표한 사람이 한명 이하일때 조크 메시지
    if len(user_id_list) == 0:
        phrase = bopbot_util.get_phrase('poll_joke')

        payload = {"token": str(bot_token), "channel": channel_id, "as_user": "false", 'text': phrase}
        print bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)

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
                                                    'Yelp_id': {'Action': 'PUT', 'Value': item['Yelp_id'].encode('utf8')},
                                                    'lat': {'Action': 'PUT', 'Value': item['location']['coordinate']['lat']},
                                                    'lng': {'Action': 'PUT', 'Value': item['location']['coordinate']['lng']},
                                                    'Message_ts': {'Action': 'PUT', 'Value': message_ts}
                                                    }
                                  )
        restaurant_attachment = bopbot_util.make_restaurant_list_attachments([item])
        restaurant_attachment = json.dumps(restaurant_attachment)

        payload = {'token': bot_token, 'channel': channel_id, 'as_user': 'false', 'text': text, 'attachments': restaurant_attachment}
        print bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)

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
        bopbot_util.send_request(conf.CHAT_POST_MESSAGE, payload)

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


# event = {u'Records': [{u'EventVersion': u'1.0', u'EventSubscriptionArn': u'arn:aws:sns:ap-northeast-1:055548510907:slack_timer:3fc7becc-6075-480f-b960-7588705b6647', u'EventSource': u'aws:sns', u'Sns': {u'SignatureVersion': u'1', u'Timestamp': u'2016-10-07T08:36:33.563Z', u'Signature': u'JtdcbgzmN0WPz3dubCTgLCyF4QF4h7JcTOJsEIPEIRwMo8m6dXx1boYBA0petG+dq+nbHphpb/ljLz2OGLIUKT8cW2SqpZO55ZOuqdP6YyDS6H1hFBT7B+Bjhewe/wCKB+l24N099yfLByQ0gTfc2yKJc6SvxApbPBcBuRyf0d1l4w//8F3Wv/ofdRgFb1hw591MCBg/oq76xCVlyRLDh0DstaSuSSaGTuA8KdY8U756szOMIeCRDKFlcQk2vsq1OM7QdkcUfMMDuJWCWoah29/YoKrbFUj4el4ztkIy6ZTQT11Rnx72He8GlzOZPamckvmSfBGYeIJhuvrKQE4mzQ==', u'SigningCertUrl': u'https://sns.ap-northeast-1.amazonaws.com/SimpleNotificationService-b95095beb82e8f6a046b3aafc7f4149a.pem', u'MessageId': u'df663576-6a1a-5965-81e7-65070acbfa77', u'Message': u'{"user_id": "U223H05MX", "channel_name": "bopbot_1475829384_41", "time": 300, "bot_token": "xoxb-88145468433-VSZ1CwT21s0mGldByFsaH8D4", "response": {"result": "{\\"ok\\":true,\\"channel\\":\\"C2LHXCS5B\\",\\"ts\\":\\"1475829392.000004\\",\\"message\\":{\\"text\\":\\"What should we eat? Vote by clicking your restaurant choice.\\",\\"username\\":\\"Test_Bopbot\\",\\"bot_id\\":\\"B2L49DS8H\\",\\"attachments\\":[{\\"text\\":\\"\\\\uace0\\\\uae30\\",\\"title\\":\\"\\\\ud64d\\\\ub3c4\\\\uc57c\\\\uc9c0\\",\\"id\\":1,\\"title_link\\":\\"http:\\\\/\\\\/www.mangoplate.com\\\\/restaurants\\\\/ORHrexBhgpif\\",\\"thumb_height\\":770,\\"thumb_width\\":1024,\\"thumb_url\\":\\"https:\\\\/\\\\/mp-seoul-image-production-s3.mangoplate.com\\\\/added_restaurants\\\\/29679_1450237707368.jpg\\",\\"color\\":\\"3aa3e3\\",\\"fallback\\":\\"NO FALLBACK DEFINED\\"},{\\"text\\":\\"\\\\uc774\\\\ud0c8\\\\ub9ac\\\\uc548\\",\\"title\\":\\"\\\\uc18c\\\\uc2a4\\\\ud0c0\\\\ub808\\",\\"id\\":2,\\"title_link\\":\\"http:\\\\/\\\\/www.mangoplate.com\\\\/restaurants\\\\/Qe5H2ZOzI0\\",\\"color\\":\\"3aa3e3\\",\\"fallback\\":\\"NO FALLBACK DEFINED\\"},{\\"text\\":\\"Chiken, \\\\ubc30\\\\ub2ec, 1\\\\uc7781\\\\ub2ed\\",\\"title\\":\\"\\\\uac15\\\\ud638\\\\ub3d9 678\\\\uce58\\\\ud0a8\\",\\"id\\":3,\\"title_link\\":\\"http:\\\\/\\\\/www.baemin.com\\\\/shop\\\\/559829\\",\\"thumb_height\\":461,\\"thumb_width\\":827,\\"thumb_url\\":\\"http:\\\\/\\\\/www.chicken678.co.kr\\\\/images\\\\/sub02\\\\/01\\\\/01.png\\",\\"color\\":\\"3aa3e3\\",\\"fallback\\":\\"NO FALLBACK DEFINED\\"},{\\"text\\":\\"\\\\uae40\\\\ubc25\\",\\"title\\":\\"\\\\ubc14\\\\ub974\\\\ub2e4\\\\uae40\\\\uc120\\\\uc0dd \\\\ub17c\\\\ud604\\\\uc544\\\\ud06c\\\\ub85c\\\\ud790\\\\uc2a4\\\\uc810\\",\\"id\\":4,\\"title_link\\":\\"http:\\\\/\\\\/www.baemin.com\\\\/shop\\\\/575099\\\\/%EB%B0%94%EB%A5%B4%EB%8B%A4%EA%B9%80%EC%84%A0%EC%83%9D-%EB%85%BC%ED%98%84%EC%95%84%ED%81%AC%EB%A1%9C%ED%9E%90%EC%8A%A4%EC%A0%90\\",\\"thumb_height\\":810,\\"thumb_width\\":1080,\\"thumb_url\\":\\"http:\\\\/\\\\/file.smartbaedal.com\\\\/fw\\\\/shopreview\\\\/2016\\\\/8\\\\/17\\\\/SB_2571248D422046131_b.jpg\\",\\"color\\":\\"3aa3e3\\",\\"fallback\\":\\"NO FALLBACK DEFINED\\"},{\\"text\\":\\"\\\\ubd80\\\\ub300\\\\ucc0c\\\\uac1c\\",\\"title\\":\\"\\\\uc774\\\\ubaa8\\\\uac00\\\\uc788\\\\ub294\\\\uc9d1\\",\\"id\\":5,\\"title_link\\":\\"http:\\\\/\\\\/www.mangoplate.com\\\\/restaurants\\\\/1Ul7Vid8aD\\",\\"color\\":\\"3aa3e3\\",\\"fallback\\":\\"NO FALLBACK DEFINED\\"},{\\"id\\":6,\\"color\\":\\"3aa3e3\\",\\"actions\\":[{\\"id\\":\\"1\\",\\"name\\":\\"\\\\ud64d\\\\ub3c4\\\\uc57c\\\\uc9c0\\",\\"text\\":\\"\\\\ud64d\\\\ub3c4\\\\uc57c\\\\uc9c0\\",\\"type\\":\\"button\\",\\"value\\":\\"{\\\\\\"Location\\\\\\": \\\\\\"mymusictastehq\\\\\\", \\\\\\"Yelp_id\\\\\\": \\\\\\"mymusictastehq_hongdoyaji\\\\\\"}\\",\\"style\\":\\"\\"},{\\"id\\":\\"2\\",\\"name\\":\\"\\\\uc18c\\\\uc2a4\\\\ud0c0\\\\ub808\\",\\"text\\":\\"\\\\uc18c\\\\uc2a4\\\\ud0c0\\\\ub808\\",\\"type\\":\\"button\\",\\"value\\":\\"{\\\\\\"Location\\\\\\": \\\\\\"mymusictastehq\\\\\\", \\\\\\"Yelp_id\\\\\\": \\\\\\"mymusictastehq_soustare\\\\\\"}\\",\\"style\\":\\"\\"},{\\"id\\":\\"3\\",\\"name\\":\\"\\\\uac15\\\\ud638\\\\ub3d9 678\\\\uce58\\\\ud0a8\\",\\"text\\":\\"\\\\uac15\\\\ud638\\\\ub3d9 678\\\\uce58\\\\ud0a8\\",\\"type\\":\\"button\\",\\"value\\":\\"{\\\\\\"Location\\\\\\": \\\\\\"mymusictastehq\\\\\\", \\\\\\"Yelp_id\\\\\\": \\\\\\"mymusictastehq_chicken_ganghodong678\\\\\\"}\\",\\"style\\":\\"\\"},{\\"id\\":\\"4\\",\\"name\\":\\"\\\\ubc14\\\\ub974\\\\ub2e4\\\\uae40\\\\uc120\\\\uc0dd \\\\ub17c\\\\ud604\\\\uc544\\\\ud06c\\\\ub85c\\\\ud790\\\\uc2a4\\\\uc810\\",\\"text\\":\\"\\\\ubc14\\\\ub974\\\\ub2e4\\\\uae40\\\\uc120\\\\uc0dd \\\\ub17c\\\\ud604\\\\uc544\\\\ud06c\\\\ub85c\\\\ud790\\\\uc2a4\\\\uc810\\",\\"type\\":\\"button\\",\\"value\\":\\"{\\\\\\"Location\\\\\\": \\\\\\"mymusictastehq\\\\\\", \\\\\\"Yelp_id\\\\\\": \\\\\\"mymusictastehq_pho10\\\\\\"}\\",\\"style\\":\\"\\"},{\\"id\\":\\"5\\",\\"name\\":\\"\\\\uc774\\\\ubaa8\\\\uac00\\\\uc788\\\\ub294\\\\uc9d1\\",\\"text\\":\\"\\\\uc774\\\\ubaa8\\\\uac00\\\\uc788\\\\ub294\\\\uc9d1\\",\\"type\\":\\"button\\",\\"value\\":\\"{\\\\\\"Location\\\\\\": \\\\\\"mymusictastehq\\\\\\", \\\\\\"Yelp_id\\\\\\": \\\\\\"mymusictastehq_budaejjigae\\\\\\"}\\",\\"style\\":\\"\\"}]}],\\"type\\":\\"message\\",\\"subtype\\":\\"bot_message\\",\\"ts\\":\\"1475829392.000004\\"}}", "success": true}, "channel": "C2LHXCS5B"}', u'MessageAttributes': {}, u'Type': u'Notification', u'UnsubscribeUrl': u'https://sns.ap-northeast-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:ap-northeast-1:055548510907:slack_timer:3fc7becc-6075-480f-b960-7588705b6647', u'TopicArn': u'arn:aws:sns:ap-northeast-1:055548510907:slack_timer', u'Subject': None}}]}
# lambda_handler(event, '')