# -*- coding: utf8 -*-
import conf
import json


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


def set_user_command_definition():
    command_table = conf.aws_dynamo_db.Table(conf.COMMAND_TABLE)

    with open('command_definition.json') as data_file:
        data = json.loads(data_file.read())
        for item in data:
            if item['status'] == 'wte_commands':
                response = command_table.put_item(Item={
                    'Status': item['status'],
                    'Commands': item['commands']
                })
            else:
                response = command_table.put_item(Item={
                    'Status': item['status'],
                    'Command_def': item['command_def'],
                    'Else': item['else']
                })
            print response


def create_tables():
    resource = conf.aws_dynamo_db
    client = conf.session.client('dynamodb')

    with open('tables.json') as data_file:
        data = json.loads(data_file.read())
        for item in data:
            name = item['TableName']
            try:
                table_description = client.describe_table(TableName=name)
                print '%s table already exists' % name
            except Exception, e:
                print '%s table does not exists' % name

                table = resource.create_table(**item)
                # wait for contirmation that the table exists
                table.meta.client.get_waiter('table_exists').wait(TableName=name)
                print '%s table is created' % name

