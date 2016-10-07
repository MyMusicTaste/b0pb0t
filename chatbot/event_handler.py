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

# event = {u'Records': [{u'EventVersion': u'1.0', u'EventSubscriptionArn': u'arn:aws:sns:ap-northeast-1:055548510907:slack_im:e977d754-4d69-47a7-b731-2418c1fdabf2', u'EventSource': u'aws:sns', u'Sns': {u'SignatureVersion': u'1', u'Timestamp': u'2016-10-07T09:57:26.335Z', u'Signature': u'BzronGSs8umWzPDPnwdF+cHCpebDmbTx0t60EaesvFMlvHKff573LW3UafNhQd8RZf8BkuoMELE9DEAvwBZJAAs8xshy6y5hJAirCfCSRDVttDmJXE+qGdAzV8SbB6dMXLZ6v9ATMBKcm+g1sRdxCoIo3i2eJ63mTjyZcVrT/MHFpcly4fwycFIyjtGGD0KCGTPXw9Z/bzlQIiH6VvH06eLtYPWe9Pz7h9XeIw4tAj2eVCwmcuPVfjudnRLhDYL+7Si3gJati1m+4ZpVv8mq6tGjBQA3DSKRgpTd7nHatukjwsQdF4d2PgUmVVQKM7ax5YOFsx6n/2F/vUk2C5QOIA==', u'SigningCertUrl': u'https://sns.ap-northeast-1.amazonaws.com/SimpleNotificationService-b95095beb82e8f6a046b3aafc7f4149a.pem', u'MessageId': u'8b7d9717-74af-515a-b364-c7660769f46b', u'Message': u'{"body-json": "payload=%7B%22actions%22%3A%5B%7B%22name%22%3A%22Archive%22%2C%22value%22%3A%22C2LJDKUFQ%22%7D%5D%2C%22callback_id%22%3A%22archive_channel%22%2C%22team%22%3A%7B%22id%22%3A%22T2235559U%22%2C%22domain%22%3A%22kokonakslack%22%7D%2C%22channel%22%3A%7B%22id%22%3A%22D2L49DSLR%22%2C%22name%22%3A%22directmessage%22%7D%2C%22user%22%3A%7B%22id%22%3A%22U223H05MX%22%2C%22name%22%3A%22kokonak%22%7D%2C%22action_ts%22%3A%221475834245.528559%22%2C%22message_ts%22%3A%221475834235.000029%22%2C%22attachment_id%22%3A%221%22%2C%22token%22%3A%22DY3WH3105WGGaPH9P6dZ351U%22%2C%22original_message%22%3A%7B%22type%22%3A%22message%22%2C%22user%22%3A%22U2L49DSCR%22%2C%22text%22%3A%22Alright+then..+you+can+archive+the+channel+%3C%23C2LJDKUFQ%3E+now.%22%2C%22bot_id%22%3A%22B2L49DS8H%22%2C%22attachments%22%3A%5B%7B%22callback_id%22%3A%22archive_channel%22%2C%22fallback%22%3A%22archive_channel%22%2C%22id%22%3A1%2C%22color%22%3A%223aa3e3%22%2C%22actions%22%3A%5B%7B%22id%22%3A%221%22%2C%22name%22%3A%22Archive%22%2C%22text%22%3A%22Archive%22%2C%22type%22%3A%22button%22%2C%22value%22%3A%22C2LJDKUFQ%22%2C%22style%22%3A%22%22%7D%2C%7B%22id%22%3A%222%22%2C%22name%22%3A%22Later%22%2C%22text%22%3A%22Later%22%2C%22type%22%3A%22button%22%2C%22value%22%3A%22C2LJDKUFQ%22%2C%22style%22%3A%22%22%7D%5D%7D%5D%2C%22ts%22%3A%221475834235.000029%22%7D%2C%22response_url%22%3A%22https%3A%5C%2F%5C%2Fhooks.slack.com%5C%2Factions%5C%2FT2235559U%5C%2F88635893925%5C%2FZxML1BQEmnqALJ4eSwhUKJ5a%22%7D", "params": {"path": {}, "querystring": {}, "header": {"Content-Type": "application/x-www-form-urlencoded", "Via": "1.1 253721461f577318527fb5be095b5061.cloudfront.net (CloudFront)", "Accept-Encoding": "gzip,deflate", "CloudFront-Is-SmartTV-Viewer": "false", "CloudFront-Forwarded-Proto": "https", "X-Forwarded-For": "52.91.184.228, 54.182.230.19", "CloudFront-Viewer-Country": "US", "Accept": "application/json,*/*", "User-Agent": "Slackbot 1.0 (+https://api.slack.com/robots)", "Host": "6fri7r4ja2.execute-api.ap-northeast-1.amazonaws.com", "X-Forwarded-Proto": "https", "X-Amz-Cf-Id": "t6oKNSq5muZ-drb-2FO38cKwXBlOo9wnS2UWKItH7MzOoNRe5BtFkw==", "CloudFront-Is-Tablet-Viewer": "false", "X-Forwarded-Port": "443", "CloudFront-Is-Mobile-Viewer": "false", "CloudFront-Is-Desktop-Viewer": "true"}}, "stage-variables": {}, "context": {"cognito-authentication-type": "", "http-method": "POST", "account-id": "", "resource-path": "/slack_im_receiver", "authorizer-principal-id": "", "user-arn": "", "request-id": "7360d6b7-8c74-11e6-8ddb-c357559c13c9", "source-ip": "52.91.184.228", "caller": "", "api-key": "", "user-agent": "Slackbot 1.0 (+https://api.slack.com/robots)", "user": "", "cognito-identity-pool-id": "", "api-id": "6fri7r4ja2", "resource-id": "pks71i", "stage": "prod", "cognito-identity-id": "", "cognito-authentication-provider": ""}}', u'MessageAttributes': {}, u'Type': u'Notification', u'UnsubscribeUrl': u'https://sns.ap-northeast-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:ap-northeast-1:055548510907:slack_im:e977d754-4d69-47a7-b731-2418c1fdabf2', u'TopicArn': u'arn:aws:sns:ap-northeast-1:055548510907:slack_im', u'Subject': None}}]}
# lambda_handler(event, '')