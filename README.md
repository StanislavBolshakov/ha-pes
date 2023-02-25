Интеграция ПетроЭлектроСбыт для Home Assistant
==================================================

> Предоставление информации о текущем состоянии лицевого счета ПетроЭлектроСбыт
>
> Передача показаний по счётчикам
>
> ! Библиотека и сервис отправки показаний интеграции поддерживают только двухтарифные счетчики
>
> ! Библиотека и интеграция поддерживают только одну учетную записать в ЛК

## Установка

1. Скопировать каталог ```pes``` в ```custom_components```
2. Создать сенсор с токеном аутентификации 

### Пример конфигурации YAML
```yaml
sensor:
  - platform: pes
    name: "PES"
    token: "c2VjcmV0X3Rva2VuCg"
```

### Способы получить токен

1. Python script
```python
import requests

url = 'https://ikus.pesc.ru/application/v3/auth/login'
headers = {'accept-encoding': 'gzip', 'content-type': 'application/json', 'rs': 'ma'}
data = '{"username":"88005553535","password":"DerPassword"}'
response = requests.post(url, headers=headers, data=data)
token = response.json().get('access_token')
print (token)
```

2. DevTools 

Открыть в любом браузере Developer Tools, добавить фильтр access_token и перезагрузить страницу личного кабинета.

## Сервисы

Интеграция регистрирует два сервиса для каждого счетчика: ```indication_raw_updater``` и ```indication_incremental_updater``` которые позволяют отправлять как "сырые" данные в виде новых абсолютных показаний, так и, соответственно, инкрементные данные. 