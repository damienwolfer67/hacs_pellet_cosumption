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

## [0.2.0] - 2025-05-12

### Added
- **Micronova AGUA IoT integration** for automatic consumption tracking
- 8 new sensors for stove monitoring:
  - Stove status (off, start, work, temp_ok, etc.)
  - Stove power level (0-5)
  - Stove ambient temperature
  - Stove setpoint temperature
  - Stove runtime today (hours)
  - **Estimated consumption (stove)** - Automatic calculation based on runtime and power level
  - Stove alarms
  - Stove pellets low sensor
- Config flow options for Micronova:
  - Enable/disable Micronova integration
  - Stove IP address
  - Consumption rates per power level (customizable kg/h)
- Automatic consumption estimation using:
  - Power level tracking
  - Runtime sampling
  - Configurable consumption rates per power level
- Translations for all Micronova sensors and settings in all 6 languages

### Changed
- Coordinator update interval reduced from 15 minutes to 1 minute for better Micronova responsiveness
- Sensors show as unavailable when Micronova connection is lost
- Enhanced config flow with Micronova settings

### Technical
- New module `micronova.py` for Micronova WiNET protocol communication
- HTTP-based polling to stove's local network (no cloud dependency)
- Support for brands using Micronova module: Thermorossi, Moretti Design, Piazzetta, Nordica, Extraflame, Edilkamin

### Fixed
- Coordinator creation in sensor platform for proper data access

## [Unreleased]

### Planned
- Additional Micronova features (control, advanced settings)
- Historical consumption comparison (manual vs automatic)
