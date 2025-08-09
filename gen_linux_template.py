#!/usr/bin/env python3
"""
Proxmox VE Linux Template Generator

This script downloads cloud images and creates VM templates in Proxmox VE.
It replicates the functionality of the original bash script with improved
error handling, logging, and modularity.
"""

import argparse
import logging
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import time


class ProxmoxTemplateGenerator:
    """Handles the creation of Proxmox VE templates from cloud images."""
    
    def __init__(self, config: Dict):
        """
        Initialize the template generator with configuration.
        
        Args:
            config: Configuration dictionary containing SSH keyfile, username, storage, etc.
        """
        self.config = config
        self.setup_logging()
        
    def setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('template_generation.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        Execute a shell command with proper error handling.
        
        Args:
            command: List of command arguments
            check: Whether to raise CalledProcessError on non-zero exit code
            
        Returns:
            CompletedProcess object
            
        Raises:
            subprocess.CalledProcessError: If command fails and check=True
        """
        try:
            self.logger.debug(f"Executing command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                self.logger.debug(f"Command output: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(command)}")
            self.logger.error(f"Error output: {e.stderr}")
            raise
            
    def download_file(self, url: str, filename: str) -> bool:
        """
        Download a file from URL with progress tracking.
        
        Args:
            url: URL to download from
            filename: Local filename to save as
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            self.logger.info(f"Downloading {filename} from {url}")
            
            # Check if file already exists
            if os.path.exists(filename):
                self.logger.info(f"File {filename} already exists, skipping download")
                return True
                
            # Download with progress
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    if block_num % 10 == 0:  # Update every 10 blocks
                        self.logger.info(f"Download progress: {percent}%")
                        
            urllib.request.urlretrieve(url, filename, progress_hook)
            self.logger.info(f"Successfully downloaded {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download {filename}: {e}")
            return False
            
    def create_template(self, vm_id: int, vm_name: str, image_file: str) -> bool:
        """
        Create a Proxmox VE template from a cloud image.
        
        Args:
            vm_id: VM ID for the template
            vm_name: Name for the template
            image_file: Path to the cloud image file
            
        Returns:
            True if template creation successful, False otherwise
        """
        try:
            self.logger.info(f"Creating template {vm_name} (ID: {vm_id})")
            
            # Check if image file exists
            if not os.path.exists(image_file):
                self.logger.error(f"Image file {image_file} not found")
                return False
                
            # Create new VM
            self.logger.info("Creating new VM...")
            self.run_command([
                "qm", "create", str(vm_id),
                "--name", vm_name,
                "--ostype", "l26"
            ])
            
            # Configure networking
            self.logger.info("Configuring networking...")
            self.run_command([
                "qm", "set", str(vm_id),
                "--net0", "virtio,bridge=vmbr0"
            ])
            
            # Configure display
            self.run_command([
                "qm", "set", str(vm_id),
                "--serial0", "socket",
                "--vga", "serial0"
            ])
            
            # Set memory, CPU, and type defaults
            self.run_command([
                "qm", "set", str(vm_id),
                "--memory", "1024",
                "--cores", "4",
                "--cpu", "host"
            ])
            
            # Import disk image
            self.logger.info("Importing disk image...")
            import_path = f"{self.config['storage']}:0,import-from={os.path.abspath(image_file)},discard=on"
            self.run_command([
                "qm", "set", str(vm_id),
                "--scsi0", import_path
            ])
            
            # Configure boot settings
            self.run_command([
                "qm", "set", str(vm_id),
                "--boot", "order=scsi0",
                "--scsihw", "virtio-scsi-single"
            ])
            
            # Enable QEMU guest agent
            self.run_command([
                "qm", "set", str(vm_id),
                "--agent", "enabled=1,fstrim_cloned_disks=1"
            ])
            
            # Add cloud-init device
            self.run_command([
                "qm", "set", str(vm_id),
                "--ide2", f"{self.config['storage']}:cloudinit"
            ])
            
            # Configure IP settings
            self.run_command([
                "qm", "set", str(vm_id),
                "--ipconfig0", "ip6=auto,ip=dhcp"
            ])
            
            # Import SSH key
            if os.path.exists(self.config['ssh_keyfile']):
                self.run_command([
                    "qm", "set", str(vm_id),
                    "--sshkeys", self.config['ssh_keyfile']
                ])
            else:
                self.logger.warning(f"SSH keyfile {self.config['ssh_keyfile']} not found")
                
            # Set username
            self.run_command([
                "qm", "set", str(vm_id),
                "--ciuser", self.config['username']
            ])
            
            # Resize disk to 8G
            self.logger.info("Resizing disk to 8G...")
            try:
                self.run_command([
                    "qm", "disk", "resize", str(vm_id), "scsi0", "8G"
                ])
            except subprocess.CalledProcessError:
                self.logger.info("Disk resize failed (likely already larger than 8G), continuing...")
                
            # Convert to template
            self.logger.info("Converting VM to template...")
            self.run_command([
                "qm", "template", str(vm_id)
            ])
            
            # Clean up downloaded file
            self.logger.info(f"Removing downloaded file {image_file}")
            os.remove(image_file)
            
            self.logger.info(f"Successfully created template {vm_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create template {vm_name}: {e}")
            return False
            
    def get_available_images(self) -> Dict[str, Dict]:
        """
        Get dictionary of available cloud images with their configurations.
        
        Returns:
            Dictionary mapping image names to their configuration
        """
        templates_file = "templates.json"
        
        try:
            with open(templates_file, 'r') as f:
                templates = json.load(f)
                self.logger.debug(f"Loaded {len(templates)} templates from {templates_file}")
                return templates
        except FileNotFoundError:
            self.logger.error(f"Templates file {templates_file} not found")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {templates_file}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading templates from {templates_file}: {e}")
            return {}
        
    def process_image(self, image_name: str) -> bool:
        """
        Download and create template for a specific image.
        
        Args:
            image_name: Name of the image to process
            
        Returns:
            True if successful, False otherwise
        """
        images = self.get_available_images()
        
        if image_name not in images:
            self.logger.error(f"Unknown image: {image_name}")
            self.logger.info(f"Available images: {', '.join(images.keys())}")
            return False
            
        image_config = images[image_name]
        
        # Download the image
        if not self.download_file(image_config['url'], image_config['filename']):
            return False
            
        # Create the template
        return self.create_template(
            image_config['vm_id'],
            image_config['vm_name'],
            image_config['filename']
        )
        
    def process_all_images(self) -> None:
        """Download and create templates for all available images."""
        images = self.get_available_images()
        
        self.logger.info(f"Processing {len(images)} images...")
        
        for image_name in images:
            self.logger.info(f"Processing {image_name}...")
            if self.process_image(image_name):
                self.logger.info(f"Successfully processed {image_name}")
            else:
                self.logger.error(f"Failed to process {image_name}")
                
    def validate_environment(self) -> bool:
        """
        Validate that the environment is ready for template creation.
        
        Returns:
            True if environment is valid, False otherwise
        """
        # Check if qm command is available
        try:
            self.run_command(["qm", "version"], check=False)
        except FileNotFoundError:
            self.logger.error("Proxmox VE qm command not found. Are you running this on a Proxmox host?")
            return False
            
        # Check if SSH keyfile exists
        if not os.path.exists(self.config['ssh_keyfile']):
            self.logger.warning(f"SSH keyfile {self.config['ssh_keyfile']} not found")
            
        # Check if storage exists
        try:
            self.run_command(["pvesm", "status", "--storage", self.config['storage']])
        except subprocess.CalledProcessError:
            self.logger.error(f"Storage {self.config['storage']} not found or not accessible")
            return False
            
        return True


def load_config(config_file: Optional[str] = None) -> Dict:
    """
    Load configuration from file or use defaults.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    default_config = {
        "ssh_keyfile": "/root/id_rsa.pub",
        "username": "admin",
        "storage": "local-zfs"
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                default_config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            
    return default_config


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate Proxmox VE templates from cloud images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                           # Create all templates
  %(prog)s --image debian-12               # Create only Debian 12 template
  %(prog)s --config my_config.json         # Use custom config file
  %(prog)s --list                          # List available images
        """
    )
    
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Create templates for all available images"
    )
    
    parser.add_argument(
        "--image",
        type=str,
        help="Create template for specific image"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (JSON format)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available images"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate environment without creating templates"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Create generator instance
    generator = ProxmoxTemplateGenerator(config)
    
    # List available images
    if args.list:
        images = generator.get_available_images()
        if not images:
            print("No templates found. Please ensure templates.json exists and is valid.")
            sys.exit(1)
        
        print("Available images:")
        for name, config in images.items():
            description = config.get('description', 'No description available')
            print(f"  {name}: {config['vm_name']} (ID: {config['vm_id']})")
            print(f"    Description: {description}")
            print(f"    URL: {config['url']}")
            print()
        return
        
    # Validate environment
    if args.validate:
        if generator.validate_environment():
            print("Environment validation passed")
        else:
            print("Environment validation failed")
            sys.exit(1)
        return
        
    # Validate environment before proceeding
    if not generator.validate_environment():
        print("Environment validation failed. Please check the errors above.")
        sys.exit(1)
        
    # Process images
    if args.all:
        generator.process_all_images()
    elif args.image:
        if not generator.process_image(args.image):
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
