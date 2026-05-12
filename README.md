# Pellet Consumption Tracker

[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home_Assistant-2024.1.0+-blue.svg)](https://www.home-assistant.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A Home Assistant custom integration to track your wood pellet consumption for pellet stoves and boilers. Track your silo level, daily consumption, estimated autonomy, and seasonal costs.

## Features

- **Manual tracking**: Add pellets when you refill your silo
- **Multiple sensors**: Daily consumption, remaining level, autonomy estimation, cost tracking
- **Flexible configuration**: Customizable silo capacity, bag weight, and pellet price
- **Statistics**: Automatic statistics in Home Assistant for historical graphs
- **Multi-language**: English and French translations
- **Services**: Easy control via Home Assistant services

## Sensors

| Sensor | Unit | Description |
|--------|------|-------------|
| Daily Consumption (bags) | bags | Bags consumed today (resets at midnight) |
| Daily Consumption (kg) | kg | Kilograms consumed today |
| Remaining Pellets (bags) | bags | Current bags in silo |
| Remaining Pellets (kg) | kg | Current kilograms in silo |
| Remaining Pellets (%) | % | Percentage of silo capacity remaining |
| Estimated Autonomy | days | Days remaining based on 7-day average |
| Total Cost (season) | EUR | Total cost for current heating season |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add this repository URL: `https://github.com/damienwolfer67/hacs_pellet_cosumption`
5. Select "Integration" as category
6. Click "Add"
7. Search for "Pellet Consumption Tracker" and click "Install"
8. Restart Home Assistant
9. Go to "Settings" → "Devices & Services" → "Add Integration"
10. Search for "Pellet Consumption Tracker" and follow the configuration wizard

### Manual Installation

1. Copy the `custom_components/pellet_consumption` directory to your Home Assistant `custom_components` folder
2. Restart Home Assistant
3. Go to "Settings" → "Devices & Services" → "Add Integration"
4. Search for "Pellet Consumption Tracker" and follow the configuration wizard

## Configuration

During the initial setup, you'll be asked to configure:

- **Silo capacity**: Total capacity in number of bags (default: 100)
- **Bag weight**: Weight of one bag in kg (default: 15 kg)
- **Pellet price**: Price per kg in EUR (default: 0.50 €/kg)
- **Instance name**: Optional name for this instance (useful if you have multiple silos)

### Modifying Configuration

After installation, you can modify settings by:

1. Going to "Settings" → "Devices & services"
2. Click on "Pellet Consumption Tracker"
3. Click "Configure" (gear icon)

## Services

The integration provides the following services:

### `pellet_consumption.add_pellets`

Add bags of pellets to your silo.

**Parameters:**
- `bags` (number, required): Number of bags to add

**Example:**
```yaml
service: pellet_consumption.add_pellets
data:
  bags: 10
```

### `pellet_consumption.set_silo_capacity`

Change the maximum capacity of your silo.

**Parameters:**
- `bags` (number, required): New capacity in bags

**Example:**
```yaml
service: pellet_consumption.set_silo_capacity
data:
  bags: 150
```

### `pellet_consumption.set_bag_weight`

Update the weight of one pellet bag.

**Parameters:**
- `weight` (number, required): Weight in kg

**Example:**
```yaml
service: pellet_consumption.set_bag_weight
data:
  weight: 15.5
```

### `pellet_consumption.set_pellet_price`

Update the price per kg of pellets.

**Parameters:**
- `price` (number, required): Price in EUR/kg

**Example:**
```yaml
service: pellet_consumption.set_pellet_price
data:
  price: 0.55
```

### `pellet_consumption.reset_season`

Reset all seasonal statistics (cost, consumption history).

**Parameters:** None

**Example:**
```yaml
service: pellet_consumption.reset_season
data: {}
```

## Automation Examples

### Notify when autonomy is low

```yaml
alias: "Low pellet autonomy alert"
trigger:
  - platform: numeric_state
    entity_id: sensor.pellet_consumption_estimated_autonomy
    below: 7
condition: []
action:
  - service: notify.mobile_app_my_phone
    data:
      title: "Low Pellet Autonomy"
      message: "Only {{ states('sensor.pellet_consumption_estimated_autonomy') }} days of pellets remaining!"
```

### Button to add pellets

```yaml
type: custom:button-card
entity: sensor.pellet_consumption_remaining_bags
name: Add 10 Bags
icon: mdi:package-variant
tap_action:
  action: call-service
  service: pellet_consumption.add_pellets
  service_data:
    bags: 10
```

### Dashboard Card

Create a simple card for your Lovelace dashboard:

```yaml
type: vertical-stack
title: Pellet Consumption
cards:
  - type: gauge
    entity: sensor.pellet_consumption_remaining_percentage
    name: Remaining
    min: 0
    max: 100
    unit: '%'
  - type: entities
    entities:
      - entity: sensor.pellet_consumption_daily_consumption_bags
        name: Today (bags)
      - entity: sensor.pellet_consumption_daily_consumption_kg
        name: Today (kg)
      - entity: sensor.pellet_consumption_estimated_autonomy
        name: Autonomy (days)
      - entity: sensor.pellet_consumption_total_cost_season
        name: Cost (season)
```

## How Consumption is Calculated

The integration tracks consumption by monitoring the difference between pellet additions and current level:

1. When you add pellets via the `add_pellets` service, the quantity is recorded
2. At midnight each day, a snapshot is taken
3. Daily consumption = (bags at start of day) - (bags at end of day)
4. The estimated autonomy is calculated based on the average consumption of the last 7 days

This means you should only add pellets when you actually refill your silo for accurate tracking.

## Troubleshooting

### Sensors not updating

Try restarting Home Assistant after installation. The sensors should appear within a few seconds after startup.

### Wrong consumption values

Make sure you're only calling the `add_pellets` service when you physically add pellets to your silo. The integration calculates consumption based on the difference between additions and current level.

### Autonomy seems incorrect

The autonomy is calculated based on a 7-day rolling average. After initial installation, it may take a few days to get accurate estimates. You can manually adjust the silo capacity if needed.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Created by [@damienwolfer67](https://github.com/damienwolfer67)

## Support

If you encounter any issues, please [open an issue](https://github.com/damienwolfer67/hacs_pellet_cosumption/issues) on GitHub.
