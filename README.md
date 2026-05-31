# BDS Server Renewal Script

A Python script to automatically backup, update, and restart your Minecraft Bedrock Dedicated Server (BDS).

## Features

- ✅ Automatic backup of worlds and configurations
- ✅ Preserves custom files and directories
- ✅ **Fully configurable preserved files list**
- ✅ Downloads and installs latest BDS version
- ✅ Automatic restart with screen
- ✅ Cleanup of old backups
- ✅ Dry-run mode for safety
- ✅ Interactive prompts for confirmation

## What Gets Preserved

The script automatically preserves these files and directories during update:

### Configuration Files
- `server.properties` - Main server configuration
- `permissions.json` - Player permissions/operator list
- `whitelist.json` - Whitelist configuration
- `allowlist.json` - Alternative whitelist format

### Custom Content
- `textures/` - Custom textures
- `world_templates/` - World templates
- `behavior_packs/` - Custom behavior packs
- `resource_packs/` - Custom resource packs
- `plugins/` - Server plugins (if supported)

### World Data
- `worlds/` - All world data (backed up separately)

### ⚙️ Customizable Preserved Items

**You can add your own files and folders to preserve!** Just edit the `preserved_items` list in `config.json`:

```json
{
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
        "plugins",
        "YOUR_CUSTOM_FILE.txt",
        "YOUR_CUSTOM_FOLDER"
    ]
}
```

### Example: Adding Custom Files

If you have additional files to preserve, just add them to the `preserved_items` list:

```json
"preserved_items": [
    "server.properties",
    "permissions.json",
    "my_custom_config.cfg",
    "custom_scripts",
    "backup_settings.json"
]
```

## Installation

### 1. Upload files to your Ubuntu server

```bash
scp renew_bds.py config.json requirements.txt user@your-server:/opt/bds-renew/
```

### 2. Install Python dependencies

```bash
cd /opt/bds-renew
pip3 install -r requirements.txt
```

### 3. Configure the script

Edit `config.json` to match your setup:

```json
{
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
```

## Usage

### Full renewal (recommended)
```bash
python3 renew_bds.py
```

This will:
1. Backup world data
2. Backup server properties and custom content
3. Stop the server (via screen)
4. Download latest BDS version
5. Install new version (preserving your files)
6. Restart the server

### Check for updates only
```bash
python3 renew_bds.py --check-version
```

### Preview mode (dry run)
```bash
python3 renew_bds.py --dry-run
```

Shows what would be done without making any changes.

### Skip specific steps
```bash
python3 renew_bds.py --skip-backup    # Skip backup process
python3 renew_bds.py --skip-stop      # Skip stopping server
python3 renew_bds.py --skip-start     # Skip starting server after update
```

### Create default config
```bash
python3 renew_bds.py --init
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `server_dir` | Path to BDS installation | `/opt/bedrock-server` |
| `backup_dir` | Path for backups | `/opt/bedrock-backups` |
| `screen_name` | Screen session name | `bds` |
| `world_name` | World folder name | `Bedrock level` |
| `keep_backups` | Number of backups to keep | `5` |
| `server_executable` | BDS executable name | `bedrock_server` |
| `download_url_linux` | Download URL template | Official Microsoft URL |

## Safety Features

1. **Automatic Backups** - World data is backed up before any changes
2. **Preserved Files** - Custom content is preserved during update
3. **Confirmation Prompts** - You'll be asked before continuing if backup fails
4. **Dry Run Mode** - Preview changes without executing
5. **Old Backup Cleanup** - Automatically removes old backups to save space

## Manual Backup

If you want to manually backup before running:

```bash
# Backup worlds
cp -r /opt/bedrock-server/worlds /opt/bedrock-backups/worlds_backup_$(date +%Y%m%d)

# Backup configurations
cp /opt/bedrock-server/server.properties /opt/bedrock-backups/
```

## Troubleshooting

### Screen not found
Make sure screen is installed:
```bash
sudo apt-get install screen
```

### Permission denied
Make sure you have write permissions:
```bash
sudo chown -R $USER:$USER /opt/bedrock-server
```

### Download fails
Check your internet connection and try again, or manually download and place the zip file in your server directory.

## Scheduling Automatic Updates

To schedule automatic updates, add to crontab:

```bash
crontab -e
```

Add this line to run every Sunday at 3 AM:
```
0 3 * * 0 /usr/bin/python3 /opt/bds-renew/renew_bds.py >> /var/log/bds-renew.log 2>&1
```

## Requirements

- Python 3.6+
- `requests` library
- `screen` (Linux/Unix)
- Internet connection for downloading updates

## License

This script is provided as-is for educational and personal use.

## Support

For issues or feature requests, please check the script code or modify it according to your needs.
