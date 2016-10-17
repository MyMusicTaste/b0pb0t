# -*- coding: utf8 -*-
from boto3.session import Session
from yelp.oauth1_authenticator import Oauth1Authenticator

## UPDATE VARIABLES HERE
# AWS
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_KEY_ID = ''
REGION = ''

# YELP
YELP_CONSUMER_KEY = ''
YELP_CONSUMER_SECRET = ''
YELP_TOKEN= ''
YELP_TOKEN_SECRET = ''

# SNS TOPIC
aws_sns_event_arn = ''
aws_sns_im_arn = ''
aws_sns_timer_arn = ''

# SLACK
CLIENT_ID = ''
CLIENT_SECRET = ''
VERIFY_TOKEN = ''
## END VARS


# DYNAMODB TABLE NAMES
CHANNEL_POLL_TABLE = 'Channel_poll'
SLACK_TEAM_TABLE = "SlackTeamBot"
RESTAURANT_TABLE = 'Restaurant_list'
USER_STATUS_TABLE = 'User_status'
VOTE_TABLE = 'Vote_table'
BOT_PHRASES = 'Bot_phrases'


# SLACK REQUEST URL
OAUTH_ACCESS = 'https://slack.com/api/oauth.access'
CHAT_POST_MESSAGE = 'https://slack.com/api/chat.postMessage'
CHAT_UPDATE = 'https://slack.com/api/chat.update'


# RESTAURANT_TABLE - tutorial partition key
TUTORIAL_DEFAULT_RESTAURANT_LOCATION = 'tutorial_default_location'


lambda_functions = [
    'slack_event_handler',
    'slack_oauth',
    'slack_im_receiver',
    'slack_event_receiver',
    'slack_poll_timer'
]

VOTE_DURATION = 300

auth = Oauth1Authenticator(
    consumer_key=YELP_CONSUMER_KEY,
    consumer_secret=YELP_CONSUMER_SECRET,
    token=YELP_TOKEN,
    token_secret=YELP_TOKEN_SECRET
)


session = Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY_ID,
    region_name=REGION)
aws_dynamo_db = session.resource('dynamodb')
aws_sns = session.client('sns')
