"""
Quick test script to validate all data files
"""
import json
import os
from pathlib import Path

def test_json_file(filepath, description):
    """Test if JSON file is valid and print summary"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✅ {description}")
        print(f"   File: {filepath}")

        # Print specific metrics based on file type
        if 'products' in data:
            print(f"   Products: {len(data['products'])}")
            print(f"   Categories: {set(p['category'] for p in data['products'])}")

        elif 'festivals' in data:
            print(f"   Festivals: {len(data['festivals'])}")
            print(f"   Impact levels: {data.get('metadata', {}).get('impact_levels', {})}")

        elif 'distributors' in data:
            print(f"   Distributors: {len(data['distributors'])}")
            for dist in data['distributors']:
                print(f"     - {dist['name']}: {len(dist.get('products', {}))} products")

        elif 'product_abbreviations' in data:
            print(f"   Abbreviations: {len(data['product_abbreviations'])}")
            print(f"   Payment types: {len(data.get('payment_abbreviations', {}))}")

        elif 'store_id' in data:
            print(f"   Store: {data['name']}")
            print(f"   Owner: {data['owner_name']}")
            print(f"   Inventory items: {len(data.get('current_inventory', {}))}")
            print(f"   Udhaar customers: {len(data.get('udhaar_ledger', {}))}")
            total_outstanding = sum(customer['total_outstanding'] for customer in data.get('udhaar_ledger', {}).values())
            print(f"   Total udhaar outstanding: ₹{total_outstanding}")

        print()
        return True

    except json.JSONDecodeError as e:
        print(f"❌ {description}")
        print(f"   Error: Invalid JSON - {e}")
        print()
        return False
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Error: {e}")
        print()
        return False


def main():
    print("=" * 60)
    print("KiranaGPT Backend - Data Files Validation")
    print("=" * 60)
    print()

    data_dir = Path("data")

    tests = [
        (data_dir / "products.json", "Products Catalog"),
        (data_dir / "festivals.json", "Festivals Calendar"),
        (data_dir / "distributors.json", "Distributors Database"),
        (data_dir / "abbreviations.json", "Product Abbreviations"),
        (data_dir / "stores" / "sharma_general_store.json", "Sharma General Store Profile"),
    ]

    results = []
    for filepath, description in tests:
        result = test_json_file(filepath, description)
        results.append(result)

    print("=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    if all(results):
        print("✅ All data files are valid!")
        return 0
    else:
        print("❌ Some data files have errors")
        return 1


if __name__ == "__main__":
    exit(main())
