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

headers = {'Accept': 'application/json, text/plain, */*', 'Captcha': 'none','Content-Type': 'application/json',}
data = {'type': 'PHONE', 'login': '88005553535', 'password': 'DerPassword',}
response = requests.post('https://ikus.pesc.ru/api/v6/users/auth', headers=headers, json=data)
print (response.json().get('auth'))
```

2. DevTools 

Открыть в любом браузере Developer Tools и в личном кабинете посмотреть Bearer Token в хедерах GET запросов.

## Сервисы

Интеграция регистрирует два сервиса для каждого счетчика: ```indication_raw_updater``` и ```indication_incremental_updater``` которые позволяют отправлять как "сырые" данные в виде новых абсолютных показаний, так и, соответственно, инкрементные данные. 