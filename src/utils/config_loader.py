import yaml
from pathlib import Path
from src.utils.logger import logger

def load_yaml(filename: str) -> dict:
    """
    Load YAML configuration file from the config directory.
    
    Args:
        filename: Name of the YAML file to load
        
    Returns:
        Dictionary containing the parsed YAML content
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
    """
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / filename
        
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file '{filename}' not found")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
            logger.info(f"Successfully loaded config file: {filename}")
            return content
            
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {filename}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading config file {filename}: {str(e)}")
        raise