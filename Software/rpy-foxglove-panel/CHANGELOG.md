# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-08-08

### Changed
- **Roll direction corrected**: Rolling right now shows positive values (negated input)
- **Pitch direction corrected**: Pitching up now shows positive values (negated input)
- **Pitch gauge now works like an attitude indicator**:
  - 0° is horizontal at 3 o'clock (horizon reference)
  - +90° at top (nose up)
  - -90° at bottom (nose down)
  - ±180° at left
- **Tick mark labels corrected for standard mode**: 0° at top (12 o'clock), +90° at right (3 o'clock), 180° at bottom (6 o'clock), -90° at left (9 o'clock)
- **Tick mark labels for attitude mode**: 0° at right (horizon), +90° at top (nose up), -90° at bottom (nose down), ±180° at left

### Added
- Attitude indicator mode for pitch visualization
- Mode selector for gauges (standard vs attitude)

## [1.0.0] - 2026-08-08

### Added
- Initial release of RPY Visualization Panel
- Three circular gauges for Roll, Pitch, and Yaw visualization
- Custom SVG-based gauge components with zero dependencies
- Aerospace color coding (Red/Green/Blue for Roll/Pitch/Yaw)
- Topic selection dropdown with auto-detection
- Real-time data updates from ROS messages
- Support for -180° to +180° degree range
- Numeric value displays with exact angles
- Last update timestamp display
- Graceful handling of undefined/null message states
- Proper cleanup of subscriptions on unmount
