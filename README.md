# Proxmox VE Linux Template Generator

A Python script for automatically downloading cloud images and creating VM templates in Proxmox VE. This is a Python rewrite of the original bash script with improved error handling, logging, and modularity.

## Features

- **Modular Design**: Object-oriented approach with clear separation of concerns
- **Comprehensive Logging**: Detailed logging to both console and file
- **Error Handling**: Robust error handling with proper cleanup
- **Configuration Management**: JSON-based configuration with defaults
- **Progress Tracking**: Download progress indicators
- **Environment Validation**: Pre-flight checks for dependencies and permissions
- **Flexible Usage**: Support for single image or batch processing

## Prerequisites

- Proxmox VE host with `qm` command available
- Python 3.6 or higher
- Network access to download cloud images
- Appropriate storage configured in Proxmox VE

## Installation

1. Clone or download the script to your Proxmox VE host
2. Make the script executable:
   ```bash
   chmod +x gen_linux_template.py
   ```

## Configuration

### Default Configuration

The script uses these default values:
- SSH keyfile: `/root/id_rsa.pub`
- Username: `admin`
- Storage: `local-zfs`

### Custom Configuration

Create a JSON configuration file (e.g., `config.json`):

```json
{
    "ssh_keyfile": "/root/id_rsa.pub",
    "username": "admin",
    "storage": "local-zfs"
}
```

## Usage

### List Available Images

```bash
./gen_linux_template.py --list
```

### Validate Environment

```bash
./gen_linux_template.py --validate
```

### Create All Templates

```bash
./gen_linux_template.py --all
```

### Create Specific Template

```bash
./gen_linux_template.py --image debian-12
```

### Use Custom Configuration

```bash
./gen_linux_template.py --config my_config.json --all
```

## Available Images

The script supports the following cloud images:

- **debian-12**: Debian 12 (Bookworm) - Template ID: 902
- **debian-13**: Debian 13 (Trixie) - Template ID: 903
- **ubuntu-24.04**: Ubuntu 24.04 LTS - Template ID: 912
- **fedora-42**: Fedora 42 - Template ID: 942
- **alpine-3.22**: Alpine Linux 3.22 - Template ID: 940

## Template Configuration

Each template is created with the following settings:

- **OS Type**: Linux 2.6+ kernel
- **Memory**: 1024 MB
- **CPU**: 4 cores, host CPU type
- **Network**: virtio adapter on vmbr0 bridge
- **Display**: Serial console
- **Boot**: SCSI disk with virtio-scsi-single
- **Cloud-init**: Enabled with DHCP for IPv4 and SLAAC for IPv6
- **Disk**: 8GB minimum (expandable)
- **Guest Agent**: Enabled with fstrim support

## Logging

The script creates detailed logs in `template_generation.log` with timestamps and log levels. Console output provides real-time progress updates.

## Error Handling

The script includes comprehensive error handling:

- **Download Failures**: Network issues, file corruption
- **Command Failures**: Proxmox VE command errors
- **Permission Issues**: File access and storage permissions
- **Resource Conflicts**: VM ID conflicts, storage space
- **Environment Issues**: Missing dependencies, invalid configuration

## Comparison with Original Bash Script

### Improvements

1. **Better Error Handling**: Detailed error messages and graceful failure recovery
2. **Logging**: Comprehensive logging to file and console
3. **Modularity**: Object-oriented design with clear separation of concerns
4. **Configuration**: JSON-based configuration management
5. **Progress Tracking**: Download progress indicators
6. **Validation**: Pre-flight environment checks
7. **Flexibility**: Support for single image processing

### Maintained Functionality

- All original Proxmox VE commands and parameters
- Same cloud image sources and configurations
- Identical template settings and VM configurations
- File cleanup after template creation

## Troubleshooting

### Common Issues

1. **"qm command not found"**
   - Ensure you're running on a Proxmox VE host
   - Check PATH environment variable

2. **"Storage not found"**
   - Verify storage name in configuration
   - Check storage permissions and availability

3. **"SSH keyfile not found"**
   - Generate SSH keypair if needed
   - Update configuration with correct path

4. **"Download failed"**
   - Check network connectivity
   - Verify image URLs are accessible
   - Check available disk space

### Debug Mode

For detailed debugging, modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Security Considerations

- SSH keys should have appropriate permissions (600)
- Run script with appropriate user privileges
- Review downloaded images for integrity
- Consider using HTTPS for image downloads
- Validate configuration files before use

## Contributing

To add new images or modify configurations:

1. Update the `get_available_images()` method
2. Test with `--validate` flag
3. Test with single image processing
4. Update documentation

## License

This script is provided as-is for educational and operational purposes. Ensure compliance with Proxmox VE licensing and cloud image distribution terms.
