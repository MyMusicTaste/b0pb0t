# -*- coding: utf8 -*-
from boto3.session import Session
from yelp.oauth1_authenticator import Oauth1Authenticator

## UPDATE VARIABLES HERE
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_KEY_ID = ''
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
## END VARS



CHANNEL_POLL_TABLE = 'Channel_poll'
SLACK_TEAM_TABLE = "SlackTeamBot"
RESTAURANT_TABLE = 'Restaurant_list'
USER_STATUS_TABLE = 'User_status'
VOTE_TABLE = 'Vote_table'
BOT_PHRASES = 'Bot_phrases'


REGION = 'us-west-2'

session = Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY_ID,
    region_name=REGION)
aws_dynamo_db = session.resource('dynamodb')
aws_sns = session.client('sns')


auth = Oauth1Authenticator(
    consumer_key=YELP_CONSUMER_KEY,
    consumer_secret=YELP_CONSUMER_SECRET,
    token=YELP_TOKEN,
    token_secret=YELP_TOKEN_SECRET
)


OAUTH_ACCESS = 'https://slack.com/api/oauth.access'
CHAT_POST_MESSAGE = 'https://slack.com/api/chat.postMessage'
CHAT_UPDATE = 'https://slack.com/api/chat.update'



TUTORIAL_DEFAULT_RESTAURANT_LOCATION = 'tutorial_default_location'

tutoral_default_restaurant = [
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'Porto’s Bakery & Cafe  Claimed',
        'name': 'Porto’s Bakery & Cafe  Claimed',
        'image_url': 'https://s3-media3.fl.yelpcdn.com/bphoto/SImiaXeexW0bh1cuLHammQ/ls.jpg',
        'categories': [
            {
                'alias': 'Bakeries',
                'name': 'Bakeries'
            },
            {
                'alias': 'Cuban',
                'name': 'Cuban'
            },
            {
                'alias': 'Cafes',
                'name': 'Cafes'
            }
        ],
        'url': 'https://www.yelp.com/biz/portos-bakery-and-cafe-burbank'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'Cheese Board Pizza',
        'name': 'Cheese Board Pizza',
        'image_url': 'https://s3-media3.fl.yelpcdn.com/bphoto/UPF6ZVXgyeR63oycPnAh_A/ls.jpg',
        'categories': [
            {
                'alias': 'Pizza',
                'name': 'Pizza'
            },
            {
                'alias': 'Board Pizza',
                'name': 'Board Pizza'
            }
        ],
        'url': 'https://www.yelp.com/biz/cheese-board-pizza-berkeley'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'Paseo Caribbean Food - Fremont',
        'name': 'Paseo Caribbean Food - Fremont',
        'image_url': 'https://s3-media2.fl.yelpcdn.com/bphoto/6ssQE3h5PcGOcwKiguM4Qg/ls.jpg',
        'categories': [
            {
                'alias': 'Caribbean',
                'name': 'Caribbean'
            },
            {
                'alias': 'Cuban',
                'name': 'Cuban'
            },
            {
                'alias': 'Sandwiches',
                'name': 'Sandwiches'
            }
        ],
        'url': 'http://www.yelp.com/biz/paseo-seattle-3'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'Joe’s Kansas City BBQ',
        'name': 'Joe’s Kansas City BBQ',
        'image_url': 'https://s3-media2.fl.yelpcdn.com/bphoto/-cuxLpd6U2S1RMt8fdJasQ/ls.jpg',
        'categories': [
            {
                'alias': 'Barbeque',
                'name': 'Barbeque'
            }
        ],
        'url': 'https://www.yelp.com/biz/joes-kansas-city-bbq-kansas-city-2'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'Citywok',
        'name': 'Citywok',
        'image_url': 'http://vignette1.wikia.nocookie.net/southpark/images/b/bf/ChildAbductionIsNotFunny04.jpg/revision/latest?cb=20100414174909',
        'categories': [
            {
                'alias': 'Chinese',
                'name': 'Chinese'
            },
            {
                'alias': 'Sushi',
                'name': 'Sushi'
            }
        ],
        'url': 'http://southpark.wikia.com/wiki/City_Wok'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'TKB Bakery & Deli',
        'name': 'TKB Bakery & Deli',
        'image_url': 'https://s3-media3.fl.yelpcdn.com/bphoto/Ebi_a9cMAzoGHmOUGsu9wA/ls.jpg',
        'categories': [
            {
                'alias': 'Delis',
                'name': 'Delis'
            },
            {
                'alias': 'Bakeries',
                'name': 'Bakeries'
            },
            {
                'alias': 'Sandwiches',
                'name': 'Sandwiches'
            }
        ],
        'url': 'https://www.yelp.com/biz/tkb-bakery-and-deli-indio-2'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'The Morrison',
        'name': 'The Morrison',
        'image_url': 'https://s3-media2.fl.yelpcdn.com/bphoto/f2-73P95gY0pAVQWP6zh_w/ls.jpg',
        'categories': [
            {
                'alias': 'Gastropubs)',
                'name': 'Gastropubs'
            },
            {
                'alias': 'Burgers',
                'name': 'Burgers'
            },
            {
                'alias': 'Bars',
                'name': 'Bars'
            }
        ],
        'url': 'https://www.yelp.com/biz/the-morrison-los-angeles'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'Gary Danko',
        'name': 'Gary Danko',
        'image_url': 'https://s3-media2.fl.yelpcdn.com/bphoto/MWMKouFOmJk3DX6pIuWUwQ/ls.jpg',
        'categories': [
            {
                'alias': 'American (New)',
                'name': 'American (New)'
            }
        ],
        'url': 'https://www.yelp.com/biz/gary-danko-san-francisco'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'Mama D’s Italian Kitchen',
        'name': 'Mama D’s Italian Kitchen',
        'image_url': 'https://s3-media4.fl.yelpcdn.com/bphoto/dP4PfWCIT5CRULelpHas0g/ls.jpg',
        'categories': [
            {
                'alias': 'Italian',
                'name': 'Italian'
            }
        ],
        'url': 'https://www.yelp.com/biz/mama-ds-italian-kitchen-newport-beach'
    },
    {
        'Location': TUTORIAL_DEFAULT_RESTAURANT_LOCATION,
        'Yelp_id': 'tutorial_' + 'McDonald',
        'name': 'McDonald',
        'image_url': ' ',
        'categories': [
            {
                'alias': 'yes, we, love',
                'name': 'yes, we, love'
            },
            {
                'alias': 'mcD, avoid, french',
                'name': 'mcD, avoid, french'
            },
            {
                'alias': 'fries, and, mcf',
                'name': 'fries, and, mcf'
            }
        ],
        'url': ' '
    }
]
phrase_dict = [
    {"Key": "reminder_add", "Phrase": "When do you want to depart? Just type a time like '18:00', '6:00pm' or 'in 15 minutes'."},
    {"Key": "tutorial_auth", "Phrase": "I will be making channels for you and your hungry friends, so I need your authorization. Please authorize me:"},
    {"Key": "reminder_archive", "Phrase": "Alright then.. you can archive the channel <#%s> now."},
    {"Key": "reminder_add_invalid_input", "Phrase": "I need the time. Try something like '18:00', '6:00pm' or in '15 minutes'."},
    {"Key": "error_2", "Phrase": "shhh... I'm taking a poll now :)"},
    {"Key": "location_2", "Phrase": "Select your location by typing the number."},
    {"Key": "poll_tied", "Phrase": "%s restaurants tied. I chose %s for you."},
    {"Key": "reminder_1", "Phrase": "Restaurant decided! \n\n%s\n\nDo you want to set a reminder so nobody misses out?"},
    {"Key": "error_4", "Phrase": "OK! Just tell me whenever you don't know what to eat."},
    {"Key": "reminder_stop", "Phrase": "Ok! I'm not setting a reminder."},
    {"Key": "main_auth", "Phrase": "Remember, I need to make channels for you and your hungry friends, so I need your authorization. Please authorize me:"},
    {"Key": "reminder_added", "Phrase": "All set. I'll send direct messages to everyone at <%s>."},
    {"Key": "tutorial_2", "Phrase": "Thanks! Let's see how it works!"},
    {"Key": "error_1", "Phrase": "Sorry, I don't understand. Send me `What to eat`, then I will help you find restaurants.\n\nOr send `demo` to go through know how it works."},
    {"Key": "poll_joke", "Phrase": "Uh oh.. looks like someone is going to have a lonely dinner....."},
    {"Key": "error_8", "Phrase": "No restaurant found. try using other search keywords."},
    {"Key": "location_4", "Phrase": "Here's some tasty options for %s"},
    {"Key": "poll_result", "Phrase": "Great! %s is the winner."},
    {"Key": "channel_create", "Phrase": "bopbot_%s"},
    {"Key": "tutorial_5", "Phrase": "At this point, I'll ask you who you're going to eat with and send them the restaurant poll. Then I'll make a new channel and invite everyone.\n\nI'd do it now but..this is just a demo and I don't want to bother anyone right now. I'll be ready whenever you're hungry though!\n\nJust type `What to eat?` when you want a restaurant recommendation :)"},
    {"Key": "reminder_text", "Phrase": "Departure time!!\nLet's go to %s!"},
    {"Key": "tutorial_4", "Phrase": "You're not going to eat alone, right? How about asking your friends which restaurants they prefer?\n\nClick the 'send the poll' button."},
    {"Key": "tutorial_1", "Phrase": "Hi, I'm whattoeat bot. I will help you find good restaurants.\nSend me `What to eat?` in a direct message, and I'll get started. Oh, and you should really share me with your friends and co-workers ;)\n\nLet's start with a simple demo?"},
    {"Key": "tutorial_3", "Phrase": "These restaurants are yummy, but if you don't like them you can see more options.\n\nClick the 'more options' button."},
    {"Key": "error_5", "Phrase": "I'm sorry. I can't stop now, since you already made a channel. If you don't want to take a poll, archive the channel."},
    {"Key": "error_9", "Phrase": "Um..what? :(\nSend `stop` to end the current conversation."},
    {"Key": "invite_invalid_input", "Phrase": "That was weird..try typing the username like `@username`. If you're scared and want to start over, just send `stop`."},
    {"Key": "reminder_result", "Phrase": "The organizer set a reminder for %s."},
    {"Key": "location_1", "Phrase": "Type your location"},
    {"Key": "error_6", "Phrase": "We're going through the demo now. If you want to start over, just send `stop`."},
    {"Key": "invite", "Phrase": "Who do you want to send the poll to? Type your the person's username like `@username`."},
    {"Key": "location_3", "Phrase": "or type your location to search again."},
    {"Key": "poll_channel_generated", "Phrase": "Channel generated.. Go to <#%s>."},
    {"Key": "poll_vote", "Phrase": "What should we eat? Vote by clicking your restaurant choice."},
    {"Key": "error_7", "Phrase": "Sorry, I don't understand :( If you don't want to go through the demo, just send `stop`."},
    {"Key": "error_3", "Phrase": "I'm trying to find you some nice restaurants now. if you want to start over, just send `stop`."}
]
