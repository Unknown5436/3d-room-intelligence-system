#!/usr/bin/env python3
"""Test point cloud processing locally without API/database.

This allows testing the processing pipeline directly with a PLY file.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.processing.process_room import process_room_scan
from backend.utils.logger import setup_logging
import json

def main():
    """Test local processing of PLY file."""
    setup_logging()
    
    ply_file = "Room scan v1.ply"
    
    if not Path(ply_file).exists():
        print(f"Error: PLY file not found: {ply_file}")
        print(f"Files in current directory: {list(Path('.').glob('*.ply'))}")
        return
    
    print(f"Processing {ply_file}...")
    print("This may take 1-2 minutes depending on file size...\n")
    
    try:
        # Process the room scan
        result = process_room_scan(ply_file)
        
        print("=" * 60)
        print("PROCESSING RESULTS")
        print("=" * 60)
        
        print(f"\nPoint Cloud:")
        print(f"  Original points: {result['point_count']:,}")
        print(f"  Processed points: {result['processed_points']:,}")
        print(f"  Scan quality: {result['scan_quality']:.2f}")
        print(f"  Processing time: {result['processing_time']:.2f} seconds")
        
        print(f"\nRoom Dimensions:")
        dims = result['dimensions']
        print(f"  Length: {dims['length']:.2f}m")
        print(f"  Width: {dims['width']:.2f}m")
        print(f"  Height: {dims['height']:.2f}m")
        print(f"  Accuracy: {dims['accuracy']}")
        
        print(f"\nDetected Objects: {len(result['objects'])}")
        for i, obj in enumerate(result['objects'], 1):
            print(f"  {i}. {obj['type']} (confidence: {obj['confidence']:.2f})")
            print(f"     Position: [{obj['position'][0]:.2f}, {obj['position'][1]:.2f}, {obj['position'][2]:.2f}]")
            print(f"     Dimensions: {obj['dimensions']}")
            print(f"     Volume: {obj['volume']:.2f}m³")
        
        if result['relationships']:
            print(f"\nSpatial Relationships: {len(result['relationships'])}")
            for rel in result['relationships'][:5]:  # Show first 5
                print(f"  {rel['object1_type']} <-> {rel['object2_type']}: "
                      f"{rel['distance']:.2f}m ({rel['relationship']})")
        
        print("\n" + "=" * 60)
        print("✅ Processing completed successfully!")
        
        # Save results to JSON
        output_file = "processing_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

