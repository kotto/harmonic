#!/usr/bin/env python3
"""
Mobile Wrapper — CLI wrapper for HCV Mobile Camera Codec
Converts Python codec to command-line interface for Node.js integration
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from COMPRESSION_SOLUTIONS.HCV_MOBILE_CAMERA_CODEC.hcv_mobile_camera_codec import HCVMobileCamera


def main():
    parser = argparse.ArgumentParser(description='HCV Mobile Camera Codec CLI')
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--media-type', default='auto', choices=['auto', 'photo', 'video'],
                        help='Media type (auto-detect if auto)')
    parser.add_argument('--verbose', default='false', choices=['true', 'false'],
                        help='Verbose output')

    args = parser.parse_args()

    try:
        # Initialize codec
        verbose = args.verbose.lower() == 'true'
        codec = HCVMobileCamera(verbose=verbose)

        # Compress file
        result = codec.compress(args.input)

        # Save compressed file
        with open(args.output, 'wb') as f:
            f.write(result.compressed_data)

        # Output JSON result
        output = {
            'ok': True,
            'original_size': result.original_size,
            'compressed_size': result.compressed_size,
            'ratio': result.ratio,
            'savings': result.saving_percent,
            'time': result.speed_mbps,
            'quality': result.quality,
            'strategy': result.strategy,
            'media_type': result.media_type,
            'metadata': result.metadata
        }

        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        error_output = {
            'ok': False,
            'error': str(e)
        }
        print(json.dumps(error_output))
        sys.exit(1)


if __name__ == '__main__':
    main()
