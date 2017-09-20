import base64
import requests


REST_URL = 'https://viber.devinotele.com:444'
SEND = '/send'
CHECK_STATUS_MESSAGES = '/status'

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

    def send_text(self, address: str, text: str, subject: str, priority: str = NORMAL_PRIORITY,
                  content_type: str = CONTENT_TYPE_TEXT, validity_viber: int = 86400, sms_text: str = None,
                  sms_src_address: str = None, resend_sms: bool = False, comment: str = None,
                  validity_sms: int = None) -> ApiAnswer:

        json = self._make_json_for_send(priority=priority, address=address, content_type=content_type, subject=subject,
                                        validity_viber=validity_viber, sms_text=sms_text,
                                        sms_src_address=sms_src_address,
                                        resend_sms=resend_sms, comment=comment, validity_sms=validity_sms)

        json['messages'][0]['content']['text'] = text

        answer = self._request(SEND, self._get_auth_header(), json=json)
        return ApiAnswer.create(answer, json)

    def send_image(self, address: str, image: str, subject: str, content_type: str = CONTENT_TYPE_IMAGE,
                   priority: str = NORMAL_PRIORITY, validity_viber: int = 86400, sms_text: str = None,
                   sms_src_address: str = None, resend_sms: bool = False, comment: str = None,
                   validity_sms: int = None) -> ApiAnswer:

        json = self._make_json_for_send(priority=priority, address=address, content_type=content_type, subject=subject,
                                        validity_viber=validity_viber, sms_text=sms_text,
                                        sms_src_address=sms_src_address,
                                        resend_sms=resend_sms, comment=comment, validity_sms=validity_sms)

        json['messages'][0]['content']['imageUrl'] = image

        answer = self._request(SEND, self._get_auth_header(), json=json)
        return ApiAnswer.create(answer, json)

    def send_text_and_button(self, address: str, text: str, caption: str, action: str, image: str, subject: str,
                             priority: str = NORMAL_PRIORITY, content_type: str = CONTENT_TYPE_BUTTON,
                             validity_viber: int = 86400, sms_text: str = None, sms_src_address: str = None,
                             resend_sms: bool = False, comment: str = None, validity_sms: int = None) -> ApiAnswer:

        json = self._make_json_for_send(priority=priority, address=address, content_type=content_type, subject=subject,
                                        validity_viber=validity_viber, sms_text=sms_text,
                                        sms_src_address=sms_src_address,
                                        resend_sms=resend_sms, comment=comment, validity_sms=validity_sms)

        json['messages'][0]['content']['text'] = text
        json['messages'][0]['content']['caption'] = caption
        json['messages'][0]['content']['action'] = action
        if image:
            json['messages'][0]['content']['imageUrl'] = image

        answer = self._request(SEND, self._get_auth_header(), json=json)
        return ApiAnswer.create(answer, json)

    def check_status_messages(self, id_messages):
        json = {
            'messages': id_messages
        }

        answer = self._request(CHECK_STATUS_MESSAGES, self._get_auth_header(), json=json)
        return ApiAnswer.create(answer, json)

    def _get_auth_header(self) -> dict:
        headers = {'Authorization':
                   'Basic {}'.format(base64.b64encode('{}:{}'.format(self.login, self.password).encode()).decode())}
        return headers

    def _make_json_for_send(self, subject: str, priority: str, content_type: str, address: str, validity_viber: int,
                            sms_text: str, sms_src_address: str, resend_sms: bool, comment: str,
                            validity_sms: int) -> dict:
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
                        'content': {},
                        'validityPeriodSec': validity_viber,
                    }
                ]
        }

        if resend_sms:
            if validity_sms:
                json['smsValidityPeriodSec'] = validity_sms
            json['resendSms'] = resend_sms
            json['smsText'] = sms_text
            json['smsSrcAddress'] = sms_src_address
        if comment:
            json['messages'][0]['comment'] = comment

        return json

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
