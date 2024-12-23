![SamaraEnergo Logo](images/logo@2x.png)

Неофициальная [HACS](https://hacs.xyz/) интеграция [Home Assistant](https://www.home-assistant.io/) для работы с энергосбытовой компанией [СамараЭнерго](https://www.samaraenergo.ru/).

В настоящий момент интеграция предоставляет:

1. Сенсоры с текущей стоимостью зон тарифа, включая статистику за последние 3 года. Могут использоваться в качестве объекта стоимости в стандартной системе энергоменеджмента Home Assistant.
2. Сервис расчета стоимости электроэнергии по потреблениям зон.
3. Личный кабинет (в процессе).

## Способы установки

### HACS

Следуйте [инструкции](https://hacs.xyz/docs/faq/custom_repositories/) как добавить этот репозиторий в HACS. Затем установите из HACS привычным способом.

### Ручная установка

Скопируйте каталог `custom_components/samaraenergo` в конфигурационную директорию Home Assistant `$HA_HOME/config`, перезапустите Home Assistant.

## Поддержка

Поддержать меня и мою работу можно через [TONs](https://ton.org/): `UQCji6LsYAYrJP-Rij7SPjJcL0wkblVDmIkoWVpvP2YydnlA`.
