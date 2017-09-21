from unittest import TestCase
from unittest.mock import patch

from .. import client


class ApiAnswer(TestCase):
    def test_create(self):
        answer_data = {
            'status': 'ok',
            'messages': [{'providerId': 1, 'code': 'ok'}]
        }
        api_answer = client.ApiAnswer.create(answer_data)

        self.assertEqual(api_answer.status, answer_data['status'])
        self.assertEqual(api_answer.result, answer_data['messages'])
        self.assertEqual(api_answer.request_data, None)


@patch.object(client, 'requests')
class DevinoClient(TestCase):
    def setUp(self):
        self.client = client.DevinoClient('test_login', 'test_passw')

    def test_request_post(self, requests_mock):
        requests_mock.post.return_value.status_code = 200
        requests_mock.post.return_value.json.return_value = 'ok'
        self.assertFalse(requests_mock.post.called)

        response = self.client._request(path='/some_url/', headers={'test': 123})

        self.assertTrue(requests_mock.post.called)
        self.assertEqual(response, requests_mock.post.return_value.json.return_value)

    def test_request_error(self, requests_mock):
        error_data = {'Code': 'internal_error', 'Description': 'test error'}
        requests_mock.post.return_value.status_code = 500
        requests_mock.post.return_value.json.return_value = error_data
        self.assertFalse(requests_mock.post.called)

        exception = None
        try:
            self.client._request(path='/some_url/', headers={'test': 123})
        except client.DevinoException as ex:
            exception = ex

        self.assertTrue(requests_mock.post.called)
        self.assertIsNotNone(exception)
        self.assertEqual(exception.http_status, requests_mock.post.return_value.status_code)
        self.assertEqual(exception.error.code, error_data['Code'])
        self.assertEqual(exception.error.description, error_data['Description'])

    def test_auth_header(self, requests_mock):
        response = self.client._get_auth_header()

        self.assertEqual(response['Authorization'], 'Basic dGVzdF9sb2dpbjp0ZXN0X3Bhc3N3')

    def test_make_json(self, requests_mock):
        data = {
            'subject': 'your subject',
            'priority': client.NORMAL_PRIORITY,
            'content_type': client.CONTENT_TYPE_TEXT,
            'address': 'test phone number',
            'validity_viber': 84600,
            'sms_text': 'test sms text',
            'sms_src_address': 'test number of sender',
            'resend_sms': True,
            'comment': 'test comment',
            'validity_sms': 86400
        }

        json = self.client._make_json_for_send(**data)

        self.assertEqual(json['messages'][0]['subject'], data['subject'])
        self.assertEqual(json['messages'][0]['priority'], data['priority'])
        self.assertEqual(json['messages'][0]['type'], client.TYPE_FOR_VIBER)
        self.assertEqual(json['messages'][0]['contentType'], data['content_type'])
        self.assertEqual(json['messages'][0]['address'], data['address'])
        self.assertEqual(json['messages'][0]['content'], {})
        self.assertEqual(json['messages'][0]['validityPeriodSec'], data['validity_viber'])

        self.assertEqual(json['smsValidityPeriodSec'], data['validity_sms'])
        self.assertEqual(json['resendSms'], data['resend_sms'])
        self.assertEqual(json['smsText'], data['sms_text'])
        self.assertEqual(json['smsSrcAddress'], data['sms_src_address'])
        self.assertEqual(json['messages'][0]['comment'], data['comment'])

    def test_send_text(self, requests_mock):
        requests_mock.post.return_value.status_code = 200
        requests_mock.post.return_value.json.return_value = {'status': 'ok',
                                                             'messages': [{'providerId': 1, 'code': 'ok'}]}

        data = {
            'subject': 'your subject',
            'address': 'test phone number',
            'text': 'test text',
        }
        response = self.client.send_text(**data)
        self.assertEqual(response.result, requests_mock.post.return_value.json.return_value['messages'])

        call_args, call_kwargs = requests_mock.post.call_args
        self.assertEqual(self.client.url + client.SEND, call_args[0])
        self.assertEqual(data['text'], call_kwargs['json']['messages'][0]['content']['text'])

    def test_send_image(self, requests_mock):
        requests_mock.post.return_value.status_code = 200
        requests_mock.post.return_value.json.return_value = {'status': 'ok',
                                                             'messages': [{'providerId': 1, 'code': 'ok'}]}

        data = {
            'subject': 'your subject',
            'address': 'test phone number',
            'image': 'http://test.test/test_image.jpeg',
        }
        response = self.client.send_image(**data)
        self.assertEqual(response.result, requests_mock.post.return_value.json.return_value['messages'])

        call_args, call_kwargs = requests_mock.post.call_args
        self.assertEqual(self.client.url + client.SEND, call_args[0])
        self.assertEqual(data['image'], call_kwargs['json']['messages'][0]['content']['imageUrl'])

    def test_send_text_and_button(self, requests_mock):
        requests_mock.post.return_value.status_code = 200
        requests_mock.post.return_value.json.return_value = {'status': 'ok',
                                                             'messages': [{'providerId': 1, 'code': 'ok'}]}

        data = {
            'subject': 'your subject',
            'address': 'test phone number',
            'text': 'test text',
            'image': 'http://test.test/test_image.jpeg',
            'caption': 'test text button',
            'action': 'http://test.test/url_for_button',
        }
        response = self.client.send_text_and_button(**data)
        self.assertEqual(response.result, requests_mock.post.return_value.json.return_value['messages'])

        call_args, call_kwargs = requests_mock.post.call_args
        self.assertEqual(self.client.url + client.SEND, call_args[0])
        self.assertEqual(data['image'], call_kwargs['json']['messages'][0]['content']['imageUrl'])
        self.assertEqual(data['text'], call_kwargs['json']['messages'][0]['content']['text'])
        self.assertEqual(data['caption'], call_kwargs['json']['messages'][0]['content']['caption'])
        self.assertEqual(data['action'], call_kwargs['json']['messages'][0]['content']['action'])

    def test_check_messages(self, requests_mock):
        requests_mock.post.return_value.status_code = 200
        requests_mock.post.return_value.json.return_value = {'status': 'ok',
                                                             'messages': [{'providerId': 1, 'code': 'ok',
                                                                           "status": "read",
                                                                           "statusAt": "2016-08-10 15:28:50"}]}

        data = {
            'id_messages': [1]
        }

        response = self.client.check_status_messages(**data)
        self.assertEqual(response.result, requests_mock.post.return_value.json.return_value['messages'])

        call_args, call_kwargs = requests_mock.post.call_args
        self.assertEqual(self.client.url + client.CHECK_STATUS_MESSAGES, call_args[0])
        self.assertEqual(data['id_messages'], call_kwargs['json']['messages'])
