import argparse
import logging
import sys
from src.app import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Placeholder basketball desktop pet")
    parser.add_argument("--config", help="Path to external config.json")
    parser.add_argument("--smoke-seconds", type=float, default=0, help="Quit automatically for GUI validation")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(run(args.config, args.smoke_seconds))
