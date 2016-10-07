# -*- coding: utf8 -*-
import conf
import json
import bopbot_util
import debugTest
import sys
import event_chat_message
import bopbot_tutorial

def set_tutorial_restaurant():
    restaurant_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)

    with open('tutorial_restaurant.json') as data_file:
        data = json.loads(data_file.read())

        for item in data:
            response = restaurant_table.put_item(Item={
                'Location': item['Location'],
                'Yelp_id': item['Yelp_id'],
                'name': item['name'],
                'categories': item['categories'],
                'image_url': item['image_url'],
                'url': item['url']
            })
            print response


def set_default_bot_phrase():
    phrase_table = conf.aws_dynamo_db.Table(conf.BOT_PHRASES)

    with open('phrases.json') as data_file:
        data = json.loads(data_file.read())
        for item in data:
            response = phrase_table.put_item(Item={
                "Key": item['Key'],
                'Phrase': item['Phrase']
            })
            print response


def set_hq_mymusictaste():
    restaurant_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)

    with open('hq_default-1.json') as data_file:
        data = json.loads(data_file.read())

        for item in data:
            response = restaurant_table.put_item(Item={
                'Location': item['Location'],
                'Yelp_id': item['Yelp_id'],
                'image_url': item['image_url'],
                'categories': item['categories'],
                'location': item['location'],
                'url': item['url'],
                'name': item['name']
            })
            print response


response = bopbot_tutorial.send_start_demo_message(user_id='U223H05MX', bot_token='xoxb-88145468433-VSZ1CwT21s0mGldByFsaH8D4')
