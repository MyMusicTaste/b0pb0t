# -*- coding: utf8 -*-
import conf


def set_tutorial_restaurant():
    restaurant_table = conf.aws_dynamo_db.Table(conf.RESTAURANT_TABLE)

    for item in conf.tutoral_default_restaurant:
        response = restaurant_table.put_item(Item={
            'Location': item['Location'],
            'Yelp_id': item['Yelp_id'],
            'name': item['name'],
            'categories': item['categories'],
            'image_url': item['image_url'],
            'url': item['url']
        })
        print response


def set_phrase():
    phrase_table = conf.aws_dynamo_db.Table(conf.BOT_PHRASES)

    for item in conf.phrase_dict:
        response = phrase_table.put_item(Item={
            "Key": item['Key'],
            'Phrase': item['Phrase']
        })
        print response


set_tutorial_restaurant()
set_phrase()