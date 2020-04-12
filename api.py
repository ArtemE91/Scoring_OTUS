import functools
import json
import re
from datetime import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from dateutil import relativedelta as rdelta

from store import StorageRedis
from scoring import get_score, get_interests
from config import *



class Field:
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable


class CharField(Field):
    # type = str
    def __set__(self, instance, value):
        if value:
            if not isinstance(value, str):
                raise TypeError('Invalid Type, value {} must be of type str'.format(self.name))
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class ArgumentsField(Field):
    # type = dict
    def __set__(self, instance, value):
        if value:
            if not isinstance(value, dict):
                raise TypeError('Invalid Type, value {} must be of type dict'.format(self.name))
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class PhoneField(Field):
    # type = str or int, может быть пустым, length == 11, начинается с 7
    def __set__(self, instance, value):
        if value:
            if not isinstance(value, (str, int)):
                raise TypeError('Invalid Type, value {} must be of type str or int'.format(self.name))
            if isinstance(value, int):
                value = str(value)
            if len(value) != 11:
                raise ValueError('Invalid Length, length number must be 11 character')
            if not value.startswith('7'):
                raise ValueError('Invalid Value, phone number must begin with 7')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class EmailField(CharField):
    # type = str, может быть пустым, в строке есть @
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value and '@' not in value:
            raise ValueError('Invalid Value, email must contain a character @')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class DateField(CharField):
    # type = str, может быть пустым, datetime, format = DD.MM.YYYY
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value:
            if not re.match(r'\d{2}\.\d{2}.\d{4}', value):
                raise ValueError('Invalid Value, value format must be DD.MM.YYYY')
            if not self.valid_date(value):
                raise ValueError('Invalid Date, value must be valid date')
            value = self.valid_date(value)
        instance.__dict__[self.name] = value

    @classmethod
    def valid_date(cls, value):
        try:
            return datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            return ''

    def __set_name__(self, owner, name):
        self.name = name


class BirthDayField(DateField):
    # type = str, может быть пустым, datetime, format = DD.MM.YYYY, birth day <= 70 лет,
    # не может быть отрицательным (еще нет такой даты)
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value:
            now_date = datetime.now()
            value_date = self.valid_date(value)
            delta = rdelta.relativedelta(now_date, value_date)
            if delta.years >= 70:
                raise ValueError('Invalid Age Old, age must be under 70')
            if value_date > now_date:
                raise ValueError('Invalid Age Negative, this date has not yet arrived')
            value = instance.birthday
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class GenderField(Field):
    # type = int, может быть пустым, value = 0, 1 or 2
    def __set__(self, instance, value):
        if value:
            if not isinstance(value, int):
                raise TypeError('Invalid Type, value must be of type int')
            if value not in GENDERS:
                raise ValueError('Invalid Value, value must be 0, 1 or 2')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class ClientIDsField(Field):
    # type = list, НЕ может быть пустым, type каждого элемента = int
    def __set__(self, instance, value):
        if not isinstance(value, list):
            raise TypeError('Invalid Type, value must be of type list')
        for el in value:
            if not isinstance(el, int):
                raise TypeError('Invalid Type, value elements must be of type int')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class ValidateMethodRequest:
    def __init__(self):
        # field_classes - пользовательские атрибуты(наcледников Field) экземпляра класса
        # errors - ошибки валидации атрибутов
        self.field_classes = [obj for name, obj in self.__class__.__dict__.items() if isinstance(obj, Field)]
        self.errors = {}

    def validate(self, **kwargs):
        for field in self.field_classes:
            # Проверка пришел ли атрибут
            attr = None if field.name not in kwargs else kwargs[field.name]
            # Если атрибут обязателен но он не пришел пишем в errors
            if field.required and attr is None:
                self.errors[field.name] = 'field is required'
            else:
                # Если атрибут пришел проверяем может ли он быть пустым
                if not field.nullable and not attr:
                    # Если не может быть пустым а в атрибуте он пустой то пишем в errors
                    self.errors[field.name] = 'field cannot be empty'
                else:
                    # валидируем значение
                    try:
                        setattr(self, field.name, attr)
                    except (TypeError, ValueError) as e:
                        self.errors[field.name] = str(e)


class OnlineScoreRequest(ValidateMethodRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self, **kwargs):
        super().validate(**kwargs)
        if not self.valid_pair():
            self.errors['invalid_pairs'] = 'There must be one pair of non-empty values: {}'.format(self._str_pair())

    def valid_pair(self):
        return any((
            all((self.phone is not None, self.email is not None)),
            all((self.first_name is not None, self.last_name is not None)),
            all((self.gender is not None, self.birthday is not None))
        ))

    def _str_pair(self):
        return ', '.join(["%s:%s" % (first_arg, second_arg) for first_arg, second_arg in PAIRS])

    def get_no_empty_field(self):
        fields_name = []  # Список не пустых аргументов
        for field_name in self.field_classes:
            if getattr(self, field_name.name, None) or getattr(self, field_name.name, None) == 0:
                fields_name.append(field_name.name)
        return fields_name


class ClientsInterestsRequest(ValidateMethodRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class MethodRequest(ValidateMethodRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode()).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode()).hexdigest()
    if digest == request.token:
        return True
    return False


def auth(func):
    @functools.wraps(func)
    def decorator(request, *arg, **kwargs):
        if check_auth(request):
            return func(request, *arg, **kwargs)
        logging.error(ERRORS[FORBIDDEN])
        return ERRORS[FORBIDDEN], FORBIDDEN
    return decorator


@auth
def online_score(methodrequest, ctx, store):
    onlineScoreRequest = OnlineScoreRequest()
    onlineScoreRequest.validate(**methodrequest.arguments)
    if onlineScoreRequest.errors:
        return onlineScoreRequest.errors, INVALID_REQUEST
    ctx["has"] = onlineScoreRequest.get_no_empty_field()
    if methodrequest.is_admin:
        score = 42
    else:
        score = get_score(store, onlineScoreRequest.phone,onlineScoreRequest.email,
                                       onlineScoreRequest.birthday,onlineScoreRequest.gender,
                                       onlineScoreRequest.first_name, onlineScoreRequest.last_name)
    return {'score': score}, OK


@auth
def clients_interests(methodrequest, ctx, store):
    clientsInterests = ClientsInterestsRequest()
    clientsInterests.validate(**methodrequest.arguments)
    if clientsInterests.errors:
        logging.error(clientsInterests.errors)
        return clientsInterests.errors, INVALID_REQUEST
    ctx['nclients'] = len(clientsInterests.client_ids)
    answer = {}
    for client_id in clientsInterests.client_ids:
        answer['client_id%s' % client_id] = get_interests(store, client_id)
    return answer, OK


def method_handler(request, ctx, store):
    methods = {
        'online_score': online_score,
        'clients_interests': clients_interests
    }
    methodrequest = MethodRequest()
    methodrequest.validate(**request["body"])

    if methodrequest.errors:
        logging.error(methodrequest.errors)
        return methodrequest.errors, INVALID_REQUEST

    if methodrequest.method not in methods:
        msg = '{} method not defined'.format(methodrequest.method)
        logging.error(msg)
        return msg, NOT_FOUND

    answer, code = methods[methodrequest.method](methodrequest, ctx, store)

    return answer, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = StorageRedis(host=REDIS_HOST,
                         port=REDIS_PORT,
                         timeout_connection=TIMEOUT_CONNECTION,
                         retry_connection=RETRY_CONNECTION)

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("-r", "--redis-host", action="store", default='127.0.0.1')
    op.add_option("--redis-port", action="store", type=int, default=6379)
    op.add_option("--retry-connection", action="store", type=int, default=3)
    op.add_option("--timeout-connection", action="store", type=int, default=20)
    (opts, args) = op.parse_args()

    REDIS_HOST = opts.redis_host
    REDIS_PORT = opts.redis_port
    RETRY_CONNECTION = opts.retry_connection
    TIMEOUT_CONNECTION = opts.timeout_connection

    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
