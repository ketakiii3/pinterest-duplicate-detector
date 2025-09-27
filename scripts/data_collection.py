import json
import random
from pathlib import Path
from datetime import datetime

def main():
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pins = []
    categories = ["food", "fashion", "home-decor", "travel", "diy", "art"]
    
    # Generate 1000 sample pins
    for i in range(1000):
        pins.append({
            "pin_id": f"pin_{i:06d}",
            "title": f"Pin {i} - {random.choice(categories).title()}",
            "description": f"Description for pin {i}",
            "image_url": f"https://picsum.photos/400/600?random={i}",
            "category": random.choice(categories),
            "likes": random.randint(0, 10000),
            "saves": random.randint(0, 5000),
            "comments": random.randint(0, 500),
            "width": random.choice([400, 600, 800, 1200]),
            "height": random.choice([600, 800, 1000, 1600]),
            "source_url": f"https://example.com/pin/{i}",
            "created_at": datetime.now().isoformat(),
            "user_id": f"user_{random.randint(1, 100):03d}",
            "board_id": f"board_{random.randint(1, 50):03d}"
        })
    
    # Create duplicate clusters
    for cluster_id in range(50):
        num_duplicates = random.randint(3, 5)
        base_pin_idx = random.randint(0, len(pins) - 1)
        base_pin = pins[base_pin_idx].copy()
        
        for dup_idx in range(num_duplicates):
            dup_pin = base_pin.copy()
            dup_pin["pin_id"] = f"dup_{cluster_id}_{dup_idx}"
            dup_pin["likes"] = base_pin["likes"] + random.randint(-100, 100)
            pins.append(dup_pin)
    
    # Save
    output_path = output_dir / "raw_pins.json"
    with open(output_path, 'w') as f:
        json.dump(pins, f, indent=2)
    
    print(f"✅ Saved {len(pins)} pins to {output_path}")

if __name__ == "__main__":
    main()
