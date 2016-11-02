# -*- coding: utf8 -*-

import boto3
import botocore
import unittest
import event_chat_message
from database_manager import BopBotDatabase
import conf
from mock import MagicMock, patch, Mock
import bopbot_util
import json

bot_id = ''
bot_token = ''
team_id = ''
user_id = ''
# user access token
access_token = ''

mock_table = BopBotDatabase('foo')
mock_table.put_item_to_table = MagicMock(return_value=True)


class UnittestBotMessage(unittest.TestCase):
    def test_start_what_to_eat_flow_with_access_token(self):
        event_chat_message.user_table = mock_table
        response = event_chat_message.start_what_to_eat_flow(bot_token=bot_token, user_id=bot_id, access_token=True)
        self.assertTrue(response['ok'])

    def test_start_what_to_eat_flow_without_access_token(self):
        response = event_chat_message.start_what_to_eat_flow(bot_token=bot_token, user_id=bot_id, access_token=False)
        self.assertTrue(response['ok'])

    def test_send_wte_input_to_yelp_exception(self):
        mock = bopbot_util
        mock.send_request = MagicMock()
        mock.send_request.side_effect = Exception('Some crazy error')

        result = event_chat_message.send_wte_input_to_yelp(input='sanfrancisco')
        self.assertIsNotNone(result)

    def test_process_wte_location_input_count_0(self):
        mock = event_chat_message
        mock.send_wte_input_to_yelp = MagicMock(return_value=[])
        response = mock.process_wte_location_choice(bot_token=bot_token, user_id=bot_id, user_command='')
        self.assertTrue(response['ok'])

    def test_process_wte_location_input_count_1(self):
        mock = event_chat_message
        mock.send_wte_input_to_yelp = MagicMock(return_value=[0])
        mock.send_random_restaurant_list = MagicMock(return_value={'ok': True})
        response = mock.process_wte_location_choice(bot_token=bot_token, user_id=bot_id, user_command='')
        self.assertTrue(response['ok'])

    def test_process_wte_location_input_count_2(self):
        mock = event_chat_message
        mock.send_wte_input_to_yelp = MagicMock(return_value=[0, 1])
        mock.user_table = mock_table
        response = mock.process_wte_location_choice(bot_token=bot_token, user_id=bot_id, user_command='')
        self.assertTrue(response['ok'])

    # 테이블에 suggestion이 없을때
    def test_process_wte_location_choice_suggestion_error(self):
        mock_table.get_item_from_table = MagicMock(return_value={})
        event_chat_message.user_table = mock_table
        response = event_chat_message.process_wte_location_choice(bot_token=bot_token, user_id=bot_id, user_command='1')
        self.assertTrue(response['ok'])

    def test_process_wte_location_choice_command_error(self):
        mock = event_chat_message
        mock.send_wte_input_to_yelp = MagicMock(return_value=[])
        response = mock.process_wte_location_choice(bot_token=bot_token, user_id=bot_id, user_command='test')
        self.assertTrue(response['ok'])

    # Suggestion = []
    def test_process_wte_location_choice_count0(self):
        mock_table.get_item_from_table = MagicMock(return_value={'Suggestion': []})
        event_chat_message.user_table = mock_table
        response = event_chat_message.process_wte_location_choice(bot_token=bot_token, user_id=bot_id, user_command='1')
        self.assertTrue(response['ok'])

    def test_send_random_restaurant_list(self):
        mock_table.update_item_to_table = MagicMock(return_value=True)
        event_chat_message.user_table = mock_table
        response = event_chat_message.send_random_restaurant_list(location='tutorial', bot_token=bot_token, user_id=bot_id)
        self.assertTrue(response['ok'])

    def test_make_random_restaurant_list_with_location(self):
        # mock_table.query_items_from_table = MagicMock([])
        # event_chat_message.restaurant_table = mock_table
        event_chat_message.restaurant_table = BopBotDatabase(conf.RESTAURANT_TABLE)
        response = event_chat_message.make_random_restaurant_list_with_location(location=conf.TUTORIAL_DEFAULT_RESTAURANT_LOCATION)
        self.assertGreater(len(response), 0)

    def test_process_wte_invitation_without_user(self):
        # mock = event_chat_message
        response = event_chat_message.process_wte_invitation(bot_token=bot_token, user_id=bot_id, user_command='', access_token=False)
        self.assertTrue(response['ok'])

    def test_process_wte_invitation_without_token(self):
        response = event_chat_message.process_wte_invitation(bot_token=bot_token, user_id=bot_id, user_command='<@test>', access_token=False)
        self.assertTrue(response['ok'])

    def test_process_wte_invitation_create_channel_fail(self):
        mock = event_chat_message
        mock.send_create_channel_request = MagicMock(return_value=False)
        response = mock.process_wte_invitation(bot_token=bot_token, user_id=bot_id, user_command='<@test>', access_token=True)
        self.assertFalse(response['ok'])

    def test_process_wte_invitation_poll_failed(self):
        mock = event_chat_message
        mock.send_invite_members_to_channel = MagicMock()
        mock.send_channel_generate_message = MagicMock()
        mock.send_create_channel_request = MagicMock(return_value={'channel': {'id': 'fake', 'name': 'fake'}})
        mock.send_poll_message_request = MagicMock(return_value=False)
        response = mock.process_wte_invitation(bot_token=bot_token, user_id=bot_id, user_command='<@test>', access_token=True)
        self.assertFalse(response['ok'])

    def test_process_wte_invitation(self):
        mock = event_chat_message
        mock.send_invite_members_to_channel = MagicMock()
        mock.send_channel_generate_message = MagicMock()
        mock.send_create_channel_request = MagicMock(return_value={'channel': {'id': bot_id, 'name': 'fake'}})
        mock.send_poll_message_request = MagicMock(return_value=True)

        conf.aws_sns.publish = MagicMock(return_value=True)
        mock.user_table = mock_table

        response = mock.process_wte_invitation(bot_token=bot_token, user_id=bot_id, user_command='<@test>', access_token=True)
        self.assertTrue(response)

    def test_send_create_channel_request_without_access_token(self):
        mock_util = bopbot_util
        mock_util.send_request_to_slack = MagicMock(return_value=True)
        response = event_chat_message.send_create_channel_request(False)
        self.assertTrue(response)

    def test_send_create_channel_request_with_exception(self):
        mock_util = bopbot_util
        mock_util.send_request_to_slack.side_effect = Exception('Some crazy error')
        response = event_chat_message.send_create_channel_request('')
        self.assertFalse(response)

    def test_send_invite_members_to_channel(self):
        mock_util = bopbot_util
        mock_util.send_request_to_slack = MagicMock(return_value={'ok': True})
        response = event_chat_message.send_invite_members_to_channel('fake_token', ['qwe', 'asd', 'zxc'], 'fake_channel')
        self.assertIsNotNone(response)

    def test_send_channel_generate_message(self):
        mock_util = bopbot_util
        mock_util.send_request_to_slack = MagicMock(return_value={'ok': True})
        response = event_chat_message.send_channel_generate_message(['qwe', 'asd', 'zxc'], 'fake_token', 'fake_channel')
        self.assertIsNotNone(response)

    def test_send_poll_message_request_without_current_list(self):
        mock = event_chat_message
        mock_table.get_item_from_table = MagicMock(return_value={})
        mock.user_table = mock_table
        response = mock.send_poll_message_request(user_id=bot_id, bot_token=bot_token, channel=bot_id)
        self.assertTrue(response['ok'])

    def test_send_poll_message_request_(self):
        mock = event_chat_message
        mock_table.get_item_from_table = MagicMock(return_value={'Current_list': []})

        mock_channel_table = BopBotDatabase
        mock_channel_table.put_item_to_table = MagicMock(return_value=True)

        mock.user_table = mock_table
        response = mock.send_poll_message_request(user_id=bot_id, bot_token=bot_token, channel=bot_id)
        self.assertTrue(response['ok'])

    def test_send_reminder_process_without_channel_item(self):
        mock_table.get_item_from_table = MagicMock(return_value={})
        event_chat_message.user_table = mock_table
        response = event_chat_message.send_reminder_process(bot_token=bot_token, user_id=bot_id, user_command='', access_token=False)
        self.assertIsNone(response)

    def test_send_reminder_process_get_poll_result_fail(self):
        mock_table.get_item_from_table = MagicMock(return_value={'Channel_id': 'fake_channel'})
        event_chat_message.user_table = mock_table
        event_chat_message.get_poll_result_from_channel_table = MagicMock(return_value=None)
        response = event_chat_message.send_reminder_process(bot_token=bot_token, user_id=bot_id, user_command='', access_token=False)
        self.assertFalse(response)

    # def test_send_reminder_process(self):
    #     mock_table.get_item_from_table = MagicMock(return_value={'Channel_id': 'fake_channel', 'Message_ts': 'fake_message_ts'})
    #     event_chat_message.user_table = mock_table
    #     event_chat_message.get_poll_result_from_channel_table = MagicMock(return_value={'decision': 'fake_decision', 'lng': 'fake_lng', 'lat': 'fake_lat'})
    #
    #     mock_db = BopBotDatabase
    #     mock_db.query_items_from_table = MagicMock(return_value=[{'User_id': 'fake_user1'}, {'User_id': 'fake_user2'}])
    #
    #     response = event_chat_message.send_reminder_process(bot_token=bot_token, user_id=bot_id, user_command='', access_token=False)
    #     self.assertFalse(response)

    def test_get_poll_result_from_channel_table(self):
        mock_restaurant = BopBotDatabase('foo')
        mock_restaurant.get_item_from_table = MagicMock(return_value={
            'name': 'fake_decision',
            'location': {
                'coordinate': {
                    'lat': 'fake_lat',
                    'lng': 'fake_lng'
                }
            }
        })

        event_chat_message.restaurant_table = mock_restaurant

        mock_channel = BopBotDatabase
        mock_channel.get_item_from_table = MagicMock(return_value={'Location': 'fake_location', 'Yelp_id': 'fake_yelp_id'})

        response = event_chat_message.get_poll_result_from_channel_table('')
        self.assertIsNotNone(response)


if __name__ == "__main__":
    unittest.main()

