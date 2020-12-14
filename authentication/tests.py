from io import BytesIO
from unittest.mock import patch, call
from uuid import uuid4

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .apps import AuthConfig
from .serializers import UserSerializer


class TestUserModels(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(username='testuser', password='123change',
                                                        email='test@mail.com')

    def test_user_model_should_be_instantiated_correctly(self):
        self.assertIsInstance(self.user, self.user_model)
        self.assertEqual('testuser', self.user.username)
        self.assertEqual('test@mail.com', self.user.email)

    def test_user_model_should_have_correct_str_representation(self):
        self.assertEqual('test@mail.com', str(self.user))


class TestAuthAppConfig(TestCase):
    def test_apps(self):
        self.assertEqual(AuthConfig.name, 'authentication')
        self.assertEqual(apps.get_app_config('authentication').name, 'authentication')


class TestUserSerializerCustomMethods(TestCase):
    @patch('authentication.serializers.User.objects.create_user')
    @patch('authentication.serializers.upload_image')
    def test_upload_image_called_on_create_if_profile_image_present(self, upload_image_mock, create_user_mock):
        upload_image_mock.return_value = {'username': 'newuser', 'password': '123change', 'email': 'user@mail.com',
                                          'profile_image_uuid': uuid4()}

        payload = {'username': 'newuser', 'password': '123change', 'email': 'user@mail.com', 'profile_image': BytesIO()}
        user_serializer = UserSerializer()
        user_serializer.create(payload)

        upload_image_mock.assert_called_once()
        create_user_mock.assert_called_once_with(**upload_image_mock.return_value)

    @patch('authentication.serializers.User.objects.create_user')
    @patch('authentication.serializers.upload_image')
    def test_upload_image_not_called_on_create_if_profile_image_not_present(self, upload_image_mock, create_user_mock):
        payload = {'username': 'newuser', 'password': '123change', 'email': 'user@mail.com'}
        user_serializer = UserSerializer()
        user_serializer.create(payload)

        create_user_mock.assert_called_once_with(**payload)
        upload_image_mock.assert_not_called()

    @patch('authentication.serializers.User.save')
    @patch('authentication.serializers.upload_image')
    def test_upload_image_called_on_update_if_profile_image_present(self, upload_image_mock, save_user_mock):
        upload_image_mock.return_value = {'profile_image_uuid': uuid4()}

        payload_update = {'username': 'newuser', 'password': '123change', 'email': 'user@mail.com',
                          'profile_image': BytesIO()}
        user_serializer = UserSerializer()
        user_model = get_user_model()
        old_user = user_model(username='newuser', password='123change', email='user@mail.com')
        result = user_serializer.update(old_user, payload_update)

        upload_image_mock.assert_called_once_with(payload_update, 'profile')
        self.assertTrue(result.profile_image_uuid)
        save_user_mock.assert_called_once()
        self.assertIsInstance(result, get_user_model())

    @patch('authentication.serializers.User.save')
    @patch('authentication.serializers.delete_image')
    @patch('authentication.serializers.upload_image')
    def test_upload_image_and_delete_image_called_on_update_if_profile_image_present_and_user_had_a_profile_image(
            self, upload_image_mock, delete_image_mock, save_user_mock):
        upload_image_mock.return_value = {'profile_image_uuid': '882ef4bc-aa85-42e6-ba4c-224689357de0'}

        payload_update = {'profile_image': BytesIO()}
        user_serializer = UserSerializer()
        user_model = get_user_model()
        old_uuid = '2ba7a776-6b20-4fc5-8b9d-8d3849e5a848'
        old_user = user_model(
            username='newuser', password='123change', email='user@mail.com',
            profile_image_uuid=old_uuid)

        result = user_serializer.update(old_user, payload_update)

        upload_image_mock.assert_has_calls([
            call(payload_update, 'profile'),
        ])
        delete_image_mock.assert_called_once_with(old_uuid, 'profile')
        self.assertNotEqual(old_uuid, result.profile_image_uuid)
        save_user_mock.assert_called_once()
        self.assertIsInstance(result, get_user_model())

    @patch('authentication.serializers.make_password')
    def test_password_must_be_hashed_on_update(self, make_password_mock):
        make_password_mock.return_value = 'hash'
        payload_update = {'password': '12345678'}
        user_serializer = UserSerializer()
        user_model = get_user_model()
        old_user = user_model(username='newuser', password='oldhash', email='user@mail.com')

        result = user_serializer.update(old_user, payload_update)

        make_password_mock.assert_called_once_with('12345678')
        self.assertEqual(result.password, 'hash')


class TestUserAuth(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        user_model.objects.create_superuser(username='superuser', password='123change', email='admin@mail.com')

    def test_user_should_receive_access_and_refresh_tokens(self):
        payload = {'email': 'admin@mail.com', 'password': '123change'}
        response = self.client.post('/api/token/', payload)
        data = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(data['access'])
        self.assertTrue(data['refresh'])

    def test_user_should_receive_new_access_and_refresh_tokens(self):
        payload = {'email': 'admin@mail.com', 'password': '123change'}
        response = self.client.post('/api/token/', payload)
        refresh_token = response.data['refresh']

        payload = {'refresh': refresh_token}
        response = self.client.post('/api/token/refresh/', payload)
        data = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(data['access'])
        self.assertTrue(data['refresh'])

    def test_used_refresh_token_should_return_invalid(self):
        payload = {'email': 'admin@mail.com', 'password': '123change'}
        response = self.client.post('/api/token/', payload)
        refresh_token = response.data['refresh']

        payload = {'refresh': refresh_token}
        self.client.post('/api/token/refresh/', payload)

        payload = {'refresh': refresh_token}
        response = self.client.post('/api/token/refresh/', payload)
        data = response.data

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(data['detail'], 'Token is blacklisted')
        self.assertEqual(data['code'], 'token_not_valid')


class TestUserEndpoints(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.sample_user = user_model.objects.create_user(username='testuser', password='123change',
                                                          email='test@mail.com')

        self.sample_user_w_image = user_model.objects.create_user(username='testuser2', password='123change',
                                                                  email='test2@mail.com',
                                                                  profile_image_uuid='2ba7a776-6b20-4fc5-8b9d-8d3849e5a848')

        self.super_user = user_model.objects.create_superuser(username='superuser', password='123change',
                                                              email='admin@mail.com')

        payload = {'email': 'admin@mail.com', 'password': '123change'}
        response = self.client.post('/api/token/', payload)
        self.super_token = response.data['access']

        payload = {'email': 'test@mail.com', 'password': '123change'}
        response = self.client.post('/api/token/', payload)
        self.token = response.data['access']

    def test_post_request_should_create_new_user(self):
        payload = {'username': 'newuser', 'password': '123change', 'email': 'user@mail.com'}
        response = self.client.post('/api/user/', payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_request_should_return_all_three_users(self):
        response = self.client.get('/api/user/', HTTP_AUTHORIZATION=f'Bearer {self.super_token}')
        data = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 3)

    def test_get_request_w_id_should_return_matching_user(self):
        response = self.client.get(f'/api/user/{self.sample_user.id}/')
        data = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['id'], str(self.sample_user.id))
        self.assertEqual(data['email'], self.sample_user.email)

    def test_patch_request_should_partially_update_and_return_updated_user(self):
        payload = {'email': 'newmail@email.com'}
        response = self.client.patch(f'/api/user/{self.sample_user.id}/', payload,
                                     HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['email'], payload['email'])

    def test_delete_request_should_return_http_status_204_and_delete_user(self):
        delete_response = self.client.delete(f'/api/user/{self.sample_user.id}/',
                                             HTTP_AUTHORIZATION=f'Bearer {self.super_token}')
        get_response = self.client.get('/api/user/', HTTP_AUTHORIZATION=f'Bearer {self.super_token}')
        data = get_response.data

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(data), 2)
        self.assertTrue(all(user['id'] != self.sample_user.id for user in data))

    @patch('authentication.api.delete_image')
    def test_delete_request_should_call_http_delete_image_if_user_had_a_profile_image(self, delete_image_mock):
        delete_response = self.client.delete(f'/api/user/{self.sample_user_w_image.id}/',
                                             HTTP_AUTHORIZATION=f'Bearer {self.super_token}')

        delete_image_mock.assert_called_once_with(self.sample_user_w_image.profile_image_uuid, 'profile')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
