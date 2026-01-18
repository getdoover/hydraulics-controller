# Hydraulics Controller

<!-- ![Doover Logo](https://doover.com/wp-content/uploads/Doover-Logo-Landscape-Navy-padded-small.png) -->
<img src="https://doover.com/wp-content/uploads/Doover-Logo-Landscape-Navy-padded-small.png" alt="App Icon" style="max-width: 300px;">

**Control a set of hydraulic remotes with forward/reverse actions and priority management.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/getdoover/hydraulics-controller)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/getdoover/hydraulics-controller/blob/main/LICENSE)

[Configuration](#configuration) | [Developer](https://github.com/getdoover/hydraulics-controller/blob/main/DEVELOPMENT.md) | [Need Help?](#need-help)

<br/>

## Overview

Control a set of hydraulic remotes with forward/reverse actions and priority management.

<br/>

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| **Hydraulic Remotes** | Configuration for each remote | `Required` |
| **Max Concurrent Remotes** | Max remotes to run simultaneously | `Required` |
| **Motor Controller** | Optional motor controller app | `None` |

<br/>
## Integrations

### Tags

This app exposes the following tags for integration with other apps:

| Tag | Description |
|-----|-------------|
| `run_request_reason` | Sent to motor controller to request run |
| `{remote_key}` | Current state of each remote (forward/reverse/off) |
| `request_{remote_key}` | Incoming requests from other apps |

<br/>
This app works seamlessly with:

- **Platform Interface**: Core Doover platform component


<br/>

## Need Help?

- Email: support@doover.com
- [Community Forum](https://doover.com/community)
- [Full Documentation](https://docs.doover.com)
- [Developer Documentation](https://github.com/getdoover/hydraulics-controller/blob/main/DEVELOPMENT.md)

<br/>

## Version History

### v1.0.0 (Current)
- Initial release

<br/>

## License

This app is licensed under the [Apache License 2.0](https://github.com/getdoover/hydraulics-controller/blob/main/LICENSE).
