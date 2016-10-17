import conf
from boto3.dynamodb.conditions import Key, Attr


class BopBotDatabase:

    def __init__(self, table):
        self.table = conf.aws_dynamo_db.Table(table)

    def get_item_from_table(self, key):
        try:
            response = self.table.get_item(Key=key)
            item = response['Item']
            return item
        except Exception, e:
            print e
            return None

    def put_item_to_table(self, item):
        try:
            response = self.table.put_item(Item=item)

            resp_meta = response['ResponseMetadata']
            status_code = resp_meta['HTTPStatusCode']

            if status_code == 200:
                return True
            else:
                return False
        except Exception, e:
            print e
            return False

    def delete_item_to_table(self, key):
        try:
            response = self.table.delete_item(Key=key)

            resp_meta = response['ResponseMetadata']
            status_code = resp_meta['HTTPStatusCode']

            if status_code == 200:
                return True
            else:
                return False
        except Exception, e:
            print e
            return False

    def update_item_to_table(self, key, attribute_updates):
        try:
            response = self.table.update_item(Key=key, AttributeUpdates=attribute_updates)

            resp_meta = response['ResponseMetadata']
            status_code = resp_meta['HTTPStatusCode']

            if status_code == 200:
                return True
            else:
                return False
        except Exception, e:
            print e
            return False

    def query_items_from_table(self, query):
        try:
            response = self.table.query(KeyConditionExpression=query)
            items = response['Items']
            return items

        except Exception, e:
            print e
            return None
