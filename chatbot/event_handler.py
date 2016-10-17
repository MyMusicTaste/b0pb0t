# -*- coding: utf8 -*-
import json
import conf
import event_chat_message
import event_interactive_messages


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
        event_interactive_messages.im_handler(message)

    elif topic_arn == conf.aws_sns_event_arn:
        # chat event
        event_chat_message.chat_event_handler(message)
    else:
        return 'Bad Request: Wrong topic arn: %s' % topic_arn
