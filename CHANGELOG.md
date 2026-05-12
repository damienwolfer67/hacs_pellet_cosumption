# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-05-12

### Added
- Initial release of Pellet Consumption Tracker
- Manual tracking of pellet consumption via silo refills
- 7 sensors:
  - Daily consumption (bags and kg)
  - Remaining pellets (bags, kg, percentage)
  - Estimated autonomy (days, based on 7-day average)
  - Total cost for current heating season
- 5 services:
  - `add_pellets` - Add bags to the silo
  - `set_silo_capacity` - Set silo capacity
  - `set_bag_weight` - Set bag weight in kg
  - `set_pellet_price` - Set price per kg
  - `reset_season` - Reset seasonal statistics
- Config flow for easy setup (silo capacity, bag weight, pellet price)
- Multi-language support: French, English, German, Spanish, Italian, Dutch
- Persistent data storage using Home Assistant storage
- Automatic daily snapshots at midnight for consumption tracking
- Native Home Assistant statistics integration for historical graphs
- HACS integration with validation workflow

### Configuration
- Default silo capacity: 100 bags
- Default bag weight: 15 kg
- Default pellet price: 0.50 €/kg

### Supported Languages
- 🇫🇷 French (FR)
- 🇬🇧 English (GB, US)
- 🇩🇪 German (DE)
- 🇪🇸 Spanish (ES)
- 🇮🇹 Italian (IT)
- 🇳🇱 Dutch (NL, BE)

### Minimum Requirements
- Home Assistant 2024.1.0
- HACS 1.34.0

## [Unreleased]

### Planned
- Micronova AGUA IoT integration for automatic consumption estimation
- Automatic pellet consumption calculation based on stove runtime and power level
