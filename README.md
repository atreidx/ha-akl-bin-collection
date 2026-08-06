# Auckland Council Bin Collection

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Home Assistant custom integration that creates date sensors for the next
Auckland Council household collections:

- Rubbish
- Recycling
- Food scraps

The integration reads the public Auckland Council collection page directly, so
it does not need a separate API server. Data is refreshed every six hours.

## Installation

### HACS

1. In HACS, open **Integrations**.
2. Select the three-dot menu, then **Custom repositories**.
3. Add `https://github.com/atreidx/ha-akl-bin-collection` as an
   **Integration** repository.
4. Install **Auckland Council Bin Collection** and restart Home Assistant.

### Manual

Copy `custom_components/akl_bin_collection` into the `custom_components`
directory in your Home Assistant configuration directory, then restart Home
Assistant.

## Configuration

1. Open **Settings → Devices & services**.
2. Select **Add integration**.
3. Search for **Auckland Council Bin Collection**.
4. Enter the numeric property ID from the end of your Auckland Council URL.

For example, this URL contains property ID `12345678901`:

```text
https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/12345678901.html
```

Each property creates three date sensors. A collection type that Auckland
Council does not provide for that property remains `unknown`.

## Example automation

This example sends a notification at 6 pm when rubbish is due the following
day. Replace the entity and notification service names with yours.

```yaml
alias: Rubbish bin reminder
triggers:
  - trigger: time
    at: "18:00:00"
conditions:
  - condition: template
    value_template: >-
      {{ states('sensor.auckland_property_rubbish') ==
         (now().date() + timedelta(days=1)).isoformat() }}
actions:
  - action: notify.mobile_app_your_phone
    data:
      message: Put the rubbish bin out tonight.
mode: single
```

## Notes

This is an unofficial community integration and is not affiliated with
Auckland Council. It depends on the structure and availability of the public
Auckland Council website.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
