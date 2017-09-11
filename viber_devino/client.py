import base64
import requests


REST_URL = 'https://viber.devinotele.com:444'
SEND = '/send'
CHECK_STATUS = '/status'

TYPE_FOR_VIBER = 'viber'

LOW_PRIORITY = 'low'
NORMAL_PRIORITY = 'normal'
HIGH_PRIORITY = 'high'
VERY_HIGH_PRIORITY = 'realtime'

PRIORITIES = [LOW_PRIORITY, NORMAL_PRIORITY, HIGH_PRIORITY, VERY_HIGH_PRIORITY]

CONTENT_TYPE_TEXT = 'text'
CONTENT_TYPE_IMAGE = 'image'
CONTENT_TYPE_BUTTON = 'button'

CONTENT_TYPES = [CONTENT_TYPE_TEXT, CONTENT_TYPE_IMAGE, CONTENT_TYPE_BUTTON]


class DevinoError:
    def __init__(self, code: int, description: str):
        self.code = code
        self.description = description


class DevinoException(Exception):
    def __init__(self, message: str, http_status: int = None, error: DevinoError = None,
                 base_exception: Exception = None):
        self.message = message
        self.http_status = http_status
        self.error = error
        self.base_exception = base_exception


class ApiAnswer:
    def __init__(self, status: str, result: list, request_data: dict):
        self.status = status
        self.result = result
        self.request_data = request_data

    @classmethod
    def create(cls, answer_data: dict, request_data: dict = None):
        return cls(
            status=answer_data.get('status'),
            result=answer_data.get('messages'),
            request_data=request_data,
        )


class DevinoClient:

    def __init__(self, login: str, password: str, url: str = REST_URL):
        self.login = login
        self.password = password
        self.url = url

    def send(self, priority: str, content_type: str, address: str, subject: str, text: str = None,
             caption: str = None, action: str = None, image: str = None, sms_text: str = None,
             sms_src_address: str = None, resend_sms: bool = False, validity_viber: int = None, comment: str = None,
             validity_sms: int = None) -> ApiAnswer:
        assert priority in PRIORITIES
        assert content_type in CONTENT_TYPES

        json = {
            'messages':
                [
                    {
                        'subject': subject,
                        'priority': priority,
                        'type': TYPE_FOR_VIBER,
                        'contentType': content_type,
                        'address': address,
                        'content': {}
                    }
                ]
        }

        if resend_sms:
            if validity_sms:
                json['smsValidityPeriodSec'] = validity_sms
            json['resendSms'] = resend_sms
            json['smsText'] = sms_text
            json['smsSrcAddress'] = sms_src_address
        if validity_viber:
            json['messages'][0]['validityPeriodSec'] = validity_viber
        if comment:
            json['messages'][0]['comment'] = comment
        if text:
            json['messages'][0]['content']['text'] = text
        if caption:
            json['messages'][0]['content']['caption'] = caption
        if action:
            json['messages'][0]['content']['action'] = action
        if image:
            json['messages'][0]['content']['imageUrl'] = image

        answer = self._request(SEND, self._get_auth_header(), json=json)
        return ApiAnswer.create(answer, json)

    def _get_auth_header(self) -> dict:
        headers = {'Authorization':
                       'Basic {}'.format(base64.b64encode('{}:{}'.format(self.login, self.password).encode()).decode())}
        return headers

    def _request(self, path, headers, json=None):
        request_url = self.url + path

        try:
            response = requests.post(request_url, json=json, headers=headers)
        except requests.ConnectionError as ex:
            raise DevinoException(
                message='Ошибка соединения',
                base_exception=ex,
            )

        if 400 <= response.status_code <= 500:
            error_description = response.json()
            error = DevinoError(
                code=error_description.get('Code'),
                description=error_description.get('Description'),
            )
            raise DevinoException(
                message='Ошибка отправки post-запроса',
                http_status=response.status_code,
                error=error,
            )

        return response.json()