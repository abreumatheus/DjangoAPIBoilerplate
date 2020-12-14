import json
import time
from base64 import b64encode
from pathlib import Path
from unittest.mock import patch, call, MagicMock
from uuid import uuid4

from decouple import config
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from core.utils import delete_image, upload_image


class TestDocumentationFunctional(TestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.get(config("APP_DOCS_URL", default='http://127.0.0.1:8000/'))

    def tearDown(self):
        self.driver.quit()

    def test_books_api_in_page_title(self):
        self.assertIn("Basic API", self.driver.title)

    def test_page_displays_correct_email_address(self):
        time.sleep(3)
        self.assertTrue(self.driver.find_elements_by_link_text('abreumatheus@icloud.com'))

    def test_page_displays_correct_license_type(self):
        time.sleep(3)
        self.assertTrue(self.driver.find_elements_by_link_text('MIT License'))

    def test_authentication_is_listed(self):
        time.sleep(3)
        authentication_div = self.driver.find_element_by_id('section/Authentication')
        bearer_div = self.driver.find_element_by_id('section/Authentication/Bearer')

        self.assertTrue(authentication_div)
        self.assertTrue(bearer_div)

    def test_all_operations_listed(self):
        time.sleep(3)
        token_operations = ['token_create', 'token_refresh_create']
        user_operations = ['user_list', 'user_create', 'user_read', 'user_update', 'user_partial_update',
                           'user_delete']

        all_operations = [*token_operations, *user_operations]

        main_div = self.driver.find_element_by_class_name('api-content')

        self.assertTrue(all(main_div.find_element_by_id(f'operation/{name}') for name in all_operations))


class TestUtils(TestCase):
    @patch('core.utils.sns_client.publish')
    def test_delete_image_should_publish_sns_message(self, sns_publish_mock):
        image_id = str(uuid4())
        delete_image(image_id, 'profile')

        sns_publish_mock.assert_called_once()
        sns_publish_mock.assert_has_calls([
            call(
                TopicArn=config('IMAGE_TOPIC_ARN'),
                Message=json.dumps({'action': 'delete', 'image_id': image_id, 'image_folder': 'profile'}),
            )
        ])

    @patch('core.utils.uuid4', return_value='idmock')
    @patch('core.utils.sns_client.publish')
    def test_upload_image_should_rename_image_publish_sns_message_and_return_validated_data(self, sns_publish_mock,
                                                                                            uuid_mock):
        file_path = Path(__file__).parent / 'test_dummy_data/test_image.png'
        image_file = open(file_path, 'rb')
        uploaded_file = MagicMock(name='test_image.png')
        uploaded_file.read.return_value = image_file.read()

        image_base64 = b64encode(uploaded_file.read())
        validated_data = {'profile_image': uploaded_file}

        result = upload_image(validated_data, 'profile')
        uuid_mock.assert_called_once()
        sns_publish_mock.assert_called_once()
        sns_publish_mock.assert_has_calls([
            call(
                TopicArn=config('IMAGE_TOPIC_ARN'),
                Message=json.dumps(
                    {'action': 'upload', 'image_base64': image_base64.decode('utf-8'), 'image_id': 'idmock',
                     'image_folder': 'profile'}),
            )
        ])
        self.assertIn('profile_image_uuid', result)
        self.assertNotIn('profile_image', result)
