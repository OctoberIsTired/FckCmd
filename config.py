from pathlib import Path

APP_DIR = Path(__file__).parent
CONFIG_FILE = APP_DIR / 'launcher_config.json'

# Desired approximate tile width used to calculate number of columns
DESIRED_TILE_WIDTH = 220