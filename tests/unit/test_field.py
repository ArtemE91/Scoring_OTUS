import pytest

from api import MethodRequest, ClientsInterestsRequest, OnlineScoreRequest
from api import DateField


class TestField:
    def setup(self):
        self.method = MethodRequest()

    @pytest.mark.parametrize("value", ["test", ""])
    def test_valid_value(self, value):
        self.method.account = value
        assert getattr(self.method, 'account', None) == value

    @pytest.mark.parametrize("value", [1, ['1', '2']])
    def test_invalid_value(self, value):
        with pytest.raises(TypeError) as e:
            self.method.account = value
        assert str(e.value) == 'Invalid Type, value {} must be of type str'.format(self.method.account.name)


class TestArgumentsField:
    def setup(self):
        self.method = MethodRequest()

    @pytest.mark.parametrize("value", [{1: '1', 2: '2', 3: '3'}, {1: '1', 2: [], 3: 3}, {}])
    def test_valid_value(self, value):
        self.method.arguments = value
        assert getattr(self.method, 'arguments', None) == value

    @pytest.mark.parametrize("value", [[1, 2, 3], 123, '123'])
    def test_invalid_value(self, value):
        with pytest.raises(TypeError) as e:
            self.method.arguments = value
        assert str(e.value) == 'Invalid Type, value {} must be of type dict'.format(self.method.arguments.name)


class TestPhoneField:
    def setup(self):
        self.method = OnlineScoreRequest()

    @pytest.mark.parametrize("value", ['79234567812', 79234567812, ''])
    def test_valid_value(self, value):
        self.method.phone = value
        assert getattr(self.method, 'phone', None) == str(value)

    @pytest.mark.parametrize("value", [['79234567812'], ('79234567812', '79234567812')])
    def test_invalid_value_type(self, value):
        with pytest.raises(TypeError) as e:
            self.method.phone = value
        assert str(e.value) == 'Invalid Type, value {} must be of type str or int'.format(self.method.phone.name)

    @pytest.mark.parametrize("value", ['791723', 712830])
    def test_invalid_value_len(self, value):
        with pytest.raises(ValueError) as e:
            self.method.phone = value
        assert str(e.value) == 'Invalid Length, length number must be 11 character'

    @pytest.mark.parametrize("value", ['89234567812', 89234567812])
    def test_invalid_value_begin(self, value):
        with pytest.raises(ValueError) as e:
            self.method.phone = value
        assert str(e.value) == 'Invalid Value, phone number must begin with 7'


class TestEmailField:
    def setup(self):
        self.method = OnlineScoreRequest()

    @pytest.mark.parametrize("value", ['otus@gmail.com', ''])
    def test_invalid_value(self, value):
        self.method.email = value
        assert getattr(self.method, 'email', None) == value

    @pytest.mark.parametrize("value", [123, ['otus@mail.ru']])
    def test_invalid_value_type(self, value):
        with pytest.raises(TypeError) as e:
            self.method.email = value
        assert str(e.value) == 'Invalid Type, value {} must be of type str'.format(self.method.email.name)

    @pytest.mark.parametrize("value", ['otus.mail.ru'])
    def test_invalid_value_symbol(self, value):
        with pytest.raises(ValueError) as e:
            self.method.email = value
        assert str(e.value) == 'Invalid Value, email must contain a character @'


class TestDateField:
    def setup(self):
        self.method = ClientsInterestsRequest()

    @pytest.mark.parametrize("value", ['01.01.2000', '12.12.2018', ''])
    def test_valid_value(self, value):
        self.method.date = value
        assert getattr(self.method, 'date', None) == DateField.valid_date(value)

    @pytest.mark.parametrize("value", [11012000, ['12.12.2018']])
    def test_invalid_value_type(self, value):
        with pytest.raises(TypeError) as e:
            self.method.date = value
        assert str(e.value) == 'Invalid Type, value {} must be of type str'.format(self.method.date.name)

    @pytest.mark.parametrize("value", ["12.Feb.2018", '12.12.95', '3.4.1991'])
    def test_invalid_value_format(self, value):
        with pytest.raises(ValueError) as e:
            self.method.date = value
        assert str(e.value) == 'Invalid Value, value format must be DD.MM.YYYY'

    @pytest.mark.parametrize("value", ['32.02.2012', '12.13.2002'])
    def test_invalid_value_date(self, value):
        with pytest.raises(ValueError) as e:
            self.method.date = value
        assert str(e.value) == 'Invalid Date, value must be valid date'


class TestBirthDayField:
    def setup(self):
        self.method = OnlineScoreRequest()

    @pytest.mark.parametrize("value", ['01.01.2000', '12.12.2018', ''])
    def test_valid_value(self, value):
        self.method.birthday = value
        assert getattr(self.method, 'birthday', None) == DateField.valid_date(value)

    @pytest.mark.parametrize("value", [11012000, ['12.12.2018']])
    def test_invalid_value_type(self, value):
        with pytest.raises(TypeError) as e:
            self.method.birthday = value
        assert str(e.value) == 'Invalid Type, value {} must be of type str'.format(self.method.birthday.name)

    @pytest.mark.parametrize("value", ['12.03.1950', '02.06.1930'])
    def test_invalid_value_age(self, value):
        with pytest.raises(ValueError) as e:
            self.method.birthday = value
        assert str(e.value) == 'Invalid Age Old, age must be under 70'

    @pytest.mark.parametrize("value", ['12.03.2287', '05.12.2150'])
    def test_invalid_value_negative(self, value):
        with pytest.raises(ValueError) as e:
            self.method.birthday = value
        assert str(e.value) == 'Invalid Age Negative, this date has not yet arrived'


class TestGenderField:
    def setup(self):
        self.method = OnlineScoreRequest()

    @pytest.mark.parametrize("value", [0, 1, 2, ''])
    def test_valid_value(self, value):
        self.method.gender = value
        assert getattr(self.method, 'gender', None) == value

    @pytest.mark.parametrize("value", ['0', '1', ['1']])
    def test_invalid_value_type(self, value):
        with pytest.raises(TypeError) as e:
            self.method.gender = value
        assert str(e.value) == 'Invalid Type, value must be of type int'

    @pytest.mark.parametrize("value", [3, 4])
    def test_invalid_value(self, value):
        with pytest.raises(ValueError) as e:
            self.method.gender = value
        assert str(e.value) == 'Invalid Value, value must be 0, 1 or 2'


class TestClientIDsField:
    def setup(self):
        self.method = ClientsInterestsRequest()

    @pytest.mark.parametrize("value", [[1], [0, 1, 2]])
    def test_valid_value(self, value):
        self.method.client_ids = value
        assert getattr(self.method, 'client_ids', None) == value

    @pytest.mark.parametrize("value", [(1, 2, 3), '1, 2, 3'])
    def test_invalid_value_type(self, value):
        with pytest.raises(TypeError) as e:
            self.method.client_ids = value
        assert str(e.value) == 'Invalid Type, value must be of type list'

    @pytest.mark.parametrize("value", [[1, '2', 3], [1, (1, 2), 3]])
    def test_invalid_value_type_el(self, value):
        with pytest.raises(TypeError) as e:
            self.method.client_ids = value
        assert str(e.value) == 'Invalid Type, value elements must be of type int'








