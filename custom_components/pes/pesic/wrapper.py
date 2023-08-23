from .custom_exceptions import (
    MissingArgumentError,
    UnsupportedMeterType,
    UnsupportedArgumentError,
)
from .client import RestClient


class Client:
    def __init__(self, username: str = None, password: str = None) -> None:
        if username is None or password is None:
            raise MissingArgumentError('Username and Password must be supplied')
        self.rest_client = RestClient(username=username, password=password)

    def get_group(self):
        result = self.rest_client.get('/v3/groups')
        return result

    def get_accounts(self):
        result = self.rest_client.get(f'/v5/accounts')
        return result

    def get_group_accounts(self, group_id):
        result = self.rest_client.get(f'/v5/groups/{group_id}/accounts')
        return result

    def get_account_common(self, account_id):
        result = self.rest_client.get(f'/v4/accounts/{account_id}/common-info')
        return result

    def get_account_data(self, account_id):
        result = self.rest_client.get(f'/v5/accounts/{account_id}/data')
        return result

    def get_account_tarrif(self, account_id):
        result = self.rest_client.get(f'/v3/accounts/{account_id}/tariff')
        return result

    def prepare_meter_data(self):
        result = {
            "account_id": None,
            "account_number": None,
            "meter_id": None,
            "meter_number": None,
            "current_day": None,
            "current_night": None
        }
        result["account_id"] = self.get_accounts()[0].get('accountId')
        data = self.get_account_data(result["account_id"]).get('indicationInfo').get('subServices')

        for meter in data:
            if meter.get('scale') == 'DAY':
                result["current_day"] = meter.get('value')
            elif meter.get('scale') == 'NIGHT':
                result["current_night"] = meter.get('value')
            else:
                raise UnsupportedArgumentError(f'Unexpected data in meter scale, got "{meter.get("scale")}"')

        for param in data[0].get('dutyParameters'):
            if param.get('fieldName') == 'accountNumber':
                result["account_number"] = param.get('fieldValue')
        result["meter_id"] = data[0].get('meterId')
        result["meter_number"] = data[0].get('meterNumber')

        if not isinstance(result["account_id"], int):
            raise UnsupportedArgumentError(f'Unexpected Account ID type, got "{type(result["account_id"])}"')
        if not all(isinstance(i, str) for i in [result["account_number"], result["meter_id"], result["meter_number"]]):
            raise UnsupportedArgumentError('Unexpected data in Account Num, Meter ID or Meter Number')

        return result

    def update_meter_counters(self, values: list = None):

        if len(values) != 2:
            raise UnsupportedMeterType(f'Only two tarrifs are supprted, got {len(values)}')

        account_data = self.prepare_meter_data()
        payload = {}
        new_meter_values = []

        duty_template = [{
            'fieldName': 'serviceId',
            'fieldCode': None,
            'fieldValue': '101',
            'fieldType': None
        }, {
            'fieldName': 'providerId',
            'fieldCode': None,
            'fieldValue': '0',
            'fieldType': None
        }, {
            'fieldName': 'accountNumber',
            'fieldCode': None,
            'fieldValue': str(account_data['account_number']),
            'fieldType': None
        }]

        for value in values:
            if not isinstance(value[0], int):
                raise UnsupportedArgumentError(f'New meter value must be INT, got "{type(value[0])}')
            if value[1] not in ['DAY', 'NIGHT']:
                raise UnsupportedArgumentError(f'Supported values are DAY or NIGHT, got "{value[1]}"')
            if value[1] == 'DAY' and value[0] < account_data['current_day']:
                raise UnsupportedArgumentError(
                    f'New daily values shouldn\'t be less then current. Got "{value[0]}", current {account_data["current_day"]}'
                )
            if value[1] == 'NIGHT' and value[0] < account_data['current_night']:
                raise UnsupportedArgumentError(
                    f'New nightly values shouldn\'t be less then current. Got "{value[0]}", current {account_data["current_night"]}'
                )
            new_meter_values.append({
                'subserviceId': '1',
                'value': int(value[0]),
                'meterId': str(account_data['meter_id']),
                'dutyParameters': duty_template,
                'meterNumber': str(account_data['meter_number']),
                'scale': str(value[1])
            })

        payload = {'accountId': int(account_data['account_id']), 'newIndications': new_meter_values}

        result = self.rest_client.post('/v4/accounts/indications/declare', data=payload)
        return result
