from typing import Dict
import yaml
def get_config(file_path:str)->Dict:
    with open(file_path) as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
        return config
