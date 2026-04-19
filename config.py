import argparse
import json

def load_config(path):
    if not path:
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f'{path} not found skipping config using commands arguments')
        return {}

def parse_args():
    parser = argparse.ArgumentParser(prog="flscrape")

    parser.add_argument("-c", "--config", help="Path to config JSON")

    parser.add_argument(
        "-o", "--output-path",
        help="Output directory"
    )

    parser.add_argument(
        "-sd", "--subtraction-date",
        help="Date (YYYY-MM-DD)"
    )

    return parser.parse_args()

def merge_configs(cli_args, config):
    final = config.copy()
    for key, value in vars(cli_args).items():
        if value is not None:
            final[key.replace("-", "_")] = value
    return final

def get_config():
    args = parse_args()
    return merge_configs(args, load_config(args.config))