#!/usr/bin/env python3
"""
BDS Server Renewal Script
Automatically backup, update and restart Minecraft Bedrock Dedicated Server
"""

import os
import sys
import shutil
import zipfile
import requests
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path


class BDSRenewer:
    def __init__(self, config_file="config.json"):
        self.config = self.load_config(config_file)
        self.bds_url = "https://www.minecraft.net/en-us/download/server/bedrock"
        self.download_api = "https://minecraft.net/en-us/download/server/bedrock/"
        
    def load_config(self, config_file):
        default_config = {
            "server_dir": "/opt/bedrock-server",
            "backup_dir": "/opt/bedrock-backups",
            "screen_name": "bds",
            "world_name": "Bedrock level",
            "keep_backups": 5,
            "server_executable": "bedrock_server",
            "download_url_linux": "https://minecraft.azureedge.net/bin-linux/bedrock-server-{}.zip",
            "preserved_items": [
                "server.properties",
                "permissions.json",
                "whitelist.json",
                "allowlist.json",
                "textures",
                "world_templates",
                "behavior_packs",
                "resource_packs",
                "plugins"
            ]
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def get_latest_version(self):
        self.log("Fetching latest BDS version...")
        
        try:
            response = requests.get(self.bds_url, timeout=30)
            response.raise_for_status()
            
            import re
            pattern = r'bedrock-server-(\d+\.\d+\.\d+\.\d+)\.zip'
            matches = re.findall(pattern, response.text)
            
            if matches:
                latest_version = matches[0]
                self.log(f"Latest version found: {latest_version}")
                return latest_version
            else:
                self.log("Could not find version from page, trying alternative method...", "WARN")
                return self.get_version_alternative()
                
        except Exception as e:
            self.log(f"Error fetching version: {e}", "ERROR")
            return self.get_version_alternative()
    
    def get_version_alternative(self):
        self.log("Trying alternative version detection...")
        
        try:
            api_url = "https://bugs.mojang.com/rest/api/2/project/10200/versions"
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            versions = response.json()
            released_versions = [v for v in versions if v.get('released', False)]
            
            if released_versions:
                latest = sorted(released_versions, key=lambda x: x.get('name', ''), reverse=True)[0]
                version = latest.get('name', '')
                self.log(f"Latest version from API: {version}")
                return version
        except Exception as e:
            self.log(f"Alternative method failed: {e}", "ERROR")
        
        return None
    
    def backup_world(self):
        self.log("Starting world backup...")
        
        backup_dir = Path(self.config['backup_dir'])
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        server_dir = Path(self.config['server_dir'])
        worlds_dir = server_dir / "worlds"
        
        if not worlds_dir.exists():
            self.log(f"Worlds directory not found: {worlds_dir}", "ERROR")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"world_backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        try:
            shutil.copytree(worlds_dir, backup_path)
            self.log(f"World backed up to: {backup_path}")
            
            self.cleanup_old_backups()
            return True
        except Exception as e:
            self.log(f"Backup failed: {e}", "ERROR")
            return False
    
    def backup_server_properties(self):
        self.log("Backing up server properties...")
        
        server_dir = Path(self.config['server_dir'])
        properties_file = server_dir / "server.properties"
        
        if properties_file.exists():
            backup_dir = Path(self.config['backup_dir'])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"server_properties_{timestamp}.properties"
            
            try:
                shutil.copy(properties_file, backup_file)
                self.log(f"Server properties backed up to: {backup_file}")
                return True
            except Exception as e:
                self.log(f"Failed to backup server properties: {e}", "WARN")
                return False
        return True
    
    def cleanup_old_backups(self):
        backup_dir = Path(self.config['backup_dir'])
        keep_count = self.config['keep_backups']
        
        backups = sorted(backup_dir.glob("world_backup_*"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_backup in backups[keep_count:]:
            try:
                shutil.rmtree(old_backup)
                self.log(f"Removed old backup: {old_backup}")
            except Exception as e:
                self.log(f"Failed to remove old backup {old_backup}: {e}", "WARN")
    
    def stop_server(self):
        self.log("Stopping BDS server...")
        
        screen_name = self.config['screen_name']
        
        try:
            result = subprocess.run(
                ["screen", "-list"],
                capture_output=True,
                text=True
            )
            
            if screen_name in result.stdout:
                subprocess.run(
                    ["screen", "-S", screen_name, "-X", "quit"],
                    check=True
                )
                self.log(f"Server stopped (screen session: {screen_name})")
                return True
            else:
                self.log(f"No screen session found with name: {screen_name}")
                return True
                
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to stop server: {e}", "ERROR")
            return False
        except FileNotFoundError:
            self.log("screen command not found. Is this a Linux system with screen installed?", "ERROR")
            return False
    
    def download_server(self, version):
        self.log(f"Downloading BDS version {version}...")
        
        download_url = self.config['download_url_linux'].format(version)
        server_dir = Path(self.config['server_dir'])
        zip_path = server_dir / "bedrock-server.zip"
        
        try:
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rDownload progress: {progress:.1f}%", end='', flush=True)
            
            print()
            self.log(f"Downloaded to: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.log(f"Download failed: {e}", "ERROR")
            return None
    
    def install_server(self, zip_path):
        self.log("Installing new server version...")
        
        server_dir = Path(self.config['server_dir'])
        
        preserved_items = self.config.get('preserved_items', [])
        preserved_data = {}
        
        for filename in preserved_files:
            file_path = server_dir / filename
            if file_path.exists():
                if file_path.is_file():
                    with open(file_path, 'r') as f:
                        preserved_data[filename] = ('file', f.read())
                else:
                    shutil.copytree(file_path, server_dir / f"{filename}_backup", dirs_exist_ok=True)
                    preserved_data[filename] = ('dir', server_dir / f"{filename}_backup")
                self.log(f"Preserved: {filename}")
        
        worlds_dir = server_dir / "worlds"
        worlds_backup = None
        if worlds_dir.exists():
            worlds_backup = server_dir / "worlds_temp"
            shutil.move(str(worlds_dir), str(worlds_backup))
            self.log("Preserved worlds directory")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(server_dir)
            self.log("Extracted server files")
            
            for filename, data in preserved_data.items():
                file_path = server_dir / filename
                if data[0] == 'file':
                    with open(file_path, 'w') as f:
                        f.write(data[1])
                    self.log(f"Restored: {filename}")
                elif data[0] == 'dir':
                    backup_path = data[1]
                    if file_path.exists():
                        shutil.rmtree(str(file_path))
                    shutil.move(str(backup_path), str(file_path))
                    self.log(f"Restored: {filename}")
            
            if worlds_backup and worlds_backup.exists():
                if worlds_dir.exists():
                    shutil.rmtree(str(worlds_dir))
                shutil.move(str(worlds_backup), str(worlds_dir))
                self.log("Restored worlds directory")
            
            zip_path.unlink()
            self.log("Cleaned up zip file")
            
            server_exec = server_dir / self.config['server_executable']
            if server_exec.exists():
                os.chmod(str(server_exec), 0o755)
                self.log("Set executable permissions")
            
            return True
            
        except Exception as e:
            self.log(f"Installation failed: {e}", "ERROR")
            return False
    
    def start_server(self):
        self.log("Starting BDS server...")
        
        server_dir = Path(self.config['server_dir'])
        screen_name = self.config['screen_name']
        server_exec = self.config['server_executable']
        
        try:
            subprocess.run(
                [
                    "screen", "-dmS", screen_name,
                    f"./{server_exec}"
                ],
                cwd=server_dir,
                check=True
            )
            self.log(f"Server started in screen session: {screen_name}")
            
            subprocess.run(
                ["screen", "-list"],
                capture_output=False
            )
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to start server: {e}", "ERROR")
            return False
        except FileNotFoundError:
            self.log("screen command not found", "ERROR")
            return False
    
    def get_current_version(self):
        server_dir = Path(self.config['server_dir'])
        version_file = server_dir / "server.properties"
        
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    for line in f:
                        if line.startswith('server-version='):
                            return line.split('=')[1].strip()
            except Exception:
                pass
        return "Unknown"
    
    def renew(self, skip_backup=False, skip_stop=False, skip_start=False):
        self.log("=" * 50)
        self.log("Starting BDS Server Renewal Process")
        self.log("=" * 50)
        
        current_version = self.get_current_version()
        self.log(f"Current server version: {current_version}")
        
        latest_version = self.get_latest_version()
        if not latest_version:
            self.log("Failed to determine latest version. Aborting.", "ERROR")
            return False
        
        if current_version == latest_version:
            self.log("Server is already up to date!")
            return True
        
        if not skip_backup:
            if not self.backup_world():
                self.log("Backup failed. Continue? (y/n): ", "WARN")
                response = input().lower()
                if response != 'y':
                    return False
            
            self.backup_server_properties()
        
        if not skip_stop:
            if not self.stop_server():
                self.log("Failed to stop server. Aborting.", "ERROR")
                return False
        
        zip_path = self.download_server(latest_version)
        if not zip_path:
            return False
        
        if not self.install_server(zip_path):
            return False
        
        if not skip_start:
            if not self.start_server():
                self.log("Server installed but failed to start automatically", "WARN")
                self.log("Please start the server manually")
        
        self.log("=" * 50)
        self.log(f"BDS Server renewed successfully to version {latest_version}")
        self.log("=" * 50)
        
        return True


def create_default_config():
    default_config = {
        "server_dir": "/opt/bedrock-server",
        "backup_dir": "/opt/bedrock-backups",
        "screen_name": "bds",
        "world_name": "Bedrock level",
        "keep_backups": 5,
        "server_executable": "bedrock_server",
        "download_url_linux": "https://minecraft.azureedge.net/bin-linux/bedrock-server-{}.zip"
    }
    
    with open("config.json", 'w') as f:
        json.dump(default_config, f, indent=4)
    
    print("Created default config.json")
    print("Please edit config.json with your server settings before running the script.")


def main():
    parser = argparse.ArgumentParser(
        description="Renew Minecraft Bedrock Dedicated Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    Full renewal (backup, stop, update, start)
  %(prog)s --skip-backup      Skip backup process
  %(prog)s --init             Create default config file
  %(prog)s --check-version    Check for updates only
        """
    )
    
    parser.add_argument('--config', '-c', default='config.json',
                        help='Path to config file (default: config.json)')
    parser.add_argument('--skip-backup', action='store_true',
                        help='Skip world backup')
    parser.add_argument('--skip-stop', action='store_true',
                        help='Skip stopping the server')
    parser.add_argument('--skip-start', action='store_true',
                        help='Skip starting the server after update')
    parser.add_argument('--init', action='store_true',
                        help='Create default config file')
    parser.add_argument('--check-version', action='store_true',
                        help='Check for latest version without updating')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if args.init:
        create_default_config()
        return
    
    if not os.path.exists(args.config):
        print(f"Config file not found: {args.config}")
        print("Run with --init to create a default config file")
        sys.exit(1)
    
    renewer = BDSRenewer(args.config)
    
    if args.check_version:
        current = renewer.get_current_version()
        latest = renewer.get_latest_version()
        print(f"Current version: {current}")
        print(f"Latest version:  {latest}")
        if current == latest:
            print("Server is up to date!")
        else:
            print("Update available!")
        return
    
    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print(f"Would backup world from: {renewer.config['server_dir']}/worlds")
        print(f"Would stop screen session: {renewer.config['screen_name']}")
        print(f"Would download latest version")
        print(f"Would restart server in screen session: {renewer.config['screen_name']}")
        return
    
    success = renewer.renew(
        skip_backup=args.skip_backup,
        skip_stop=args.skip_stop,
        skip_start=args.skip_start
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
