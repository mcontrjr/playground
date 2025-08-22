#!/usr/bin/env python3
"""
Standalone utility script for testing Google Places API integration.
This script can be run independently to test the backend functionality.

Example usage:
  python places.py --health                                    # Health check
  python places.py --text "pizza restaurants in NYC"          # Text search
  python places.py --zip 90210 --categories restaurant,cafe   # Zip code search
  python places.py --list-types                                # List place types
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to Python path to access src and models modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.places_client import GooglePlacesClient, GooglePlacesAPIError
from models.requests_new import (
    NearbySearchNewRequest,
    TextSearchNewRequest,
    LocationRestriction,
    Circle,
)
from models.geocoding import ZipCodeRequest
from models.place_types import (
    PLACE_TYPES,
    POPULAR_PLACE_TYPES,
    PLACE_TYPE_CATEGORIES,
    PlaceTypeCategory,
    validate_place_type,
    suggest_place_types,
    format_place_types_help
)


async def test_health_check():
    """Test health check functionality."""
    print("\n=== Testing Health Check ===")
    
    try:
        async with GooglePlacesClient() as client:
            is_healthy = await client.health_check()
            
        if is_healthy:
            print("✅ Google Places API is accessible")
            return True
        else:
            print("❌ Google Places API is not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def test_nearby_search_new():
    """Test Nearby Search (New) API functionality."""
    print("\n=== Testing Nearby Search (New) ===")
    
    # Example: Search for restaurants near Sydney using New API
    location_restriction = LocationRestriction(
        circle=Circle(
            center={"latitude": -33.8688, "longitude": 151.2093},
            radius=1500.0
        )
    )
    
    request = NearbySearchNewRequest(
        fields=[
            "places.id", "places.displayName", "places.formattedAddress",
            "places.rating"
        ],
        location_restriction=location_restriction,
        included_types=["restaurant"],
        max_result_count=3,
        language_code="en",
        region_code="AU"
    )
    
    try:
        async with GooglePlacesClient() as client:
            response = await client.nearby_search_new(request)
            
        print(f"Found {len(response.places)} places")
        
        # Display results
        for i, place in enumerate(response.places, 1):
            name = place.display_name.text if place.display_name else place.name
            print(f"\n{i}. {name}")
            if place.short_formatted_address:
                print(f"   Address: {place.short_formatted_address}")
            if place.rating:
                print(f"   Rating: {place.rating}")
        
        return True
        
    except GooglePlacesAPIError as e:
        print(f"API Error: {e.detail}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


async def test_text_search_new():
    """Test Text Search (New) API functionality."""
    print("\n=== Testing Text Search (New) ===")
    
    # Example: Search for pizza places in Sydney using New API
    request = TextSearchNewRequest(
        text_query="pizza restaurants in Sydney",
        fields=[
            "places.id", "places.displayName", "places.formattedAddress",
            "places.rating"
        ],
        included_type="restaurant",
        max_result_count=3,
        language_code="en",
        region_code="AU"
    )
    
    try:
        async with GooglePlacesClient() as client:
            response = await client.text_search_new(request)
            
        print(f"Found {len(response.places)} places")
        
        # Display results
        for i, place in enumerate(response.places, 1):
            name = place.display_name.text if place.display_name else place.name
            print(f"\n{i}. {name}")
            if place.short_formatted_address:
                print(f"   Address: {place.short_formatted_address}")
            if place.rating:
                print(f"   Rating: {place.rating}")
        
        return True
        
    except GooglePlacesAPIError as e:
        print(f"API Error: {e.detail}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


async def search_by_text(query: str, categories: Optional[List[str]] = None, max_results: int = 10) -> bool:
    """Search places by text query."""
    print(f"\n=== Text Search: '{query}' ===")
    
    # Validate categories
    if categories:
        invalid_types = [cat for cat in categories if not validate_place_type(cat)]
        if invalid_types:
            print(f"❌ Invalid place types: {', '.join(invalid_types)}")
            print("Use --list-types to see all available types")
            return False
    
    # Build the text search request
    request_fields = [
        "places.id", "places.displayName", "places.formattedAddress",
        "places.rating", "places.types", "places.priceLevel"
    ]
    
    request = TextSearchNewRequest(
        text_query=query,
        fields=request_fields,
        included_types=categories if categories else None,
        max_result_count=min(max_results, 20),  # Google API limit
        language_code="en"
    )
    
    try:
        async with GooglePlacesClient() as client:
            response = await client.text_search_new(request)
            
        if not response.places:
            print("❌ No places found matching your search")
            return False
            
        print(f"✅ Found {len(response.places)} places:")
        
        # Display results
        for i, place in enumerate(response.places, 1):
            name = place.display_name.text if place.display_name else place.name or "Unknown"
            print(f"\n{i}. {name}")
            
            if place.short_formatted_address:
                print(f"   📍 Address: {place.short_formatted_address}")
            elif place.formatted_address:
                print(f"   📍 Address: {place.formatted_address}")
                
            if place.rating:
                stars = "⭐" * int(place.rating)
                print(f"   {stars} Rating: {place.rating}")
                
            if place.price_level:
                price = "$" * place.price_level
                print(f"   💰 Price: {price}")
                
            if place.types:
                print(f"   🏷️  Types: {', '.join(place.types[:3])}")
        
        return True
        
    except GooglePlacesAPIError as e:
        print(f"❌ API Error: {e.detail}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def search_by_zip(zip_code: str, categories: List[str], radius: float = 5000, max_results: int = 10) -> bool:
    """Search places near a zip code."""
    print(f"\n=== Zip Code Search: {zip_code} ===")
    
    # Validate categories
    invalid_types = [cat for cat in categories if not validate_place_type(cat)]
    if invalid_types:
        print(f"❌ Invalid place types: {', '.join(invalid_types)}")
        print("Use --list-types to see all available types")
        return False
    
    try:
        async with GooglePlacesClient() as client:
            # First, geocode the zip code
            zip_request = ZipCodeRequest(zip_code=zip_code)
            zip_response = await client.lookup_zip_code(zip_request)
            
            if zip_response.status != "ok":
                print(f"❌ Could not find zip code {zip_code}: {zip_response.error_message}")
                return False
            
            print(f"📍 Location: {zip_response.formatted_address}")
            print(f"🌎 Coordinates: {zip_response.latitude}, {zip_response.longitude}")
            
            # Now search for places near this location
            location_restriction = LocationRestriction(
                circle=Circle(
                    center={
                        "latitude": zip_response.latitude, 
                        "longitude": zip_response.longitude
                    },
                    radius=radius
                )
            )
            
            request_fields = [
                "places.id", "places.displayName", "places.formattedAddress",
                "places.rating", "places.types", "places.priceLevel"
            ]
            
            nearby_request = NearbySearchNewRequest(
                fields=request_fields,
                location_restriction=location_restriction,
                included_types=categories,
                max_result_count=min(max_results, 20),  # Google API limit
                language_code="en"
            )
            
            nearby_response = await client.nearby_search_new(nearby_request)
            
            if not nearby_response.places:
                print(f"❌ No {', '.join(categories)} found within {radius}m of {zip_code}")
                return False
                
            print(f"\n✅ Found {len(nearby_response.places)} places within {radius}m:")
            
            # Display results
            for i, place in enumerate(nearby_response.places, 1):
                name = place.display_name.text if place.display_name else place.name or "Unknown"
                print(f"\n{i}. {name}")
                
                if place.short_formatted_address:
                    print(f"   📍 Address: {place.short_formatted_address}")
                elif place.formatted_address:
                    print(f"   📍 Address: {place.formatted_address}")
                    
                if place.rating:
                    stars = "⭐" * int(place.rating)
                    print(f"   {stars} Rating: {place.rating}")
                    
                if place.price_level:
                    price = "$" * place.price_level
                    print(f"   💰 Price: {price}")
                    
                if place.types:
                    print(f"   🏷️  Types: {', '.join(place.types[:3])}")
            
            return True
        
    except GooglePlacesAPIError as e:
        print(f"❌ API Error: {e.detail}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def validate_and_suggest_categories(categories: List[str]) -> List[str]:
    """Validate categories and provide suggestions for invalid ones."""
    valid_categories = []
    
    for category in categories:
        if validate_place_type(category):
            valid_categories.append(category)
        else:
            print(f"⚠️  Invalid place type: '{category}'")
            suggestions = suggest_place_types(category, limit=5)
            if suggestions:
                print(f"   Did you mean: {', '.join(suggestions)}")
            else:
                print(f"   Use --list-types to see all available types")
    
    return valid_categories


def display_place_types():
    """Display available place types organized by category."""
    print("\n🏷️  Available Place Types by Category:")
    print("=" * 50)
    
    for category, types in PLACE_TYPE_CATEGORIES.items():
        category_name = category.value.replace('_', ' ').title()
        print(f"\n{category_name}:")
        # Display types in columns
        types_sorted = sorted(types)
        for i, place_type in enumerate(types_sorted):
            if i % 3 == 0 and i > 0:
                print()  # New line every 3 items
            print(f"  {place_type:<25}", end="")
        print()  # Final newline
    
    print(f"\n\n📊 Popular Types: {', '.join(POPULAR_PLACE_TYPES[:10])}")
    print(f"\n📈 Total Available: {len(PLACE_TYPES)} place types")
    print("\n💡 Tip: You can combine multiple categories with commas (e.g., restaurant,cafe,bar)")


async def main():
    """Run all tests."""
    print("Google Places API Backend Test Suite")
    print("=====================================")
    
    tests = [
        ("Health Check", test_health_check),
        ("Nearby Search (New)", test_nearby_search_new),
        ("Text Search (New)", test_text_search_new),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with unexpected error: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nSummary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The backend is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        print("\nCommon issues:")
        print("- Check that your GOOGLE_MAPS_API_KEY is set in .env")
        print("- Verify your API key has Places API enabled")
        print("- Check your internet connection")
        print("- Ensure you have sufficient API quota")


async def main_cli():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Google Places API utility for searching and testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Health check
  python places.py --health
  python places.py -h
  
  # Text search
  python places.py --text "pizza restaurants in NYC"
  python places.py -t "coffee shops" --categories cafe,restaurant
  python places.py -t "sushi" -c restaurant --max-results 5
  
  # Zip code search  
  python places.py --zip 90210 --categories restaurant,cafe
  python places.py -z 10001 -c hospital,pharmacy --radius 2000
  python places.py -z 94102 -c gym,park -r 1000 -m 15
  
  # List available place types
  python places.py --list-types
  python places.py --lt
  
  # Run test suite (no arguments)
  python places.py
        """
    )
    
    # Main action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group()
    
    action_group.add_argument(
        '--health',
        action='store_true',
        help='Run health check to verify API connectivity'
    )
    
    action_group.add_argument(
        '-t', '--text',
        type=str,
        metavar='QUERY',
        help='Search places by text query (e.g., "pizza restaurants in NYC")'
    )
    
    action_group.add_argument(
        '-z', '--zip',
        type=str,
        metavar='ZIP_CODE',
        help='Search places near a zip code (requires --categories)'
    )
    
    action_group.add_argument(
        '--list-types', '--lt',
        action='store_true',
        help='List all available place types organized by category'
    )
    
    # Optional arguments for searches
    parser.add_argument(
        '-c', '--categories',
        type=str,
        metavar='TYPE1,TYPE2',
        help='Comma-separated list of place types to filter by (e.g., restaurant,cafe,bar)'
    )
    
    parser.add_argument(
        '-r', '--radius',
        type=float,
        default=5000.0,
        metavar='METERS',
        help='Search radius in meters for zip code searches (default: 5000)'
    )
    
    parser.add_argument(
        '-m', '--max-results',
        type=int,
        default=10,
        metavar='N',
        help='Maximum number of results to return (default: 10, max: 20)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Parse categories if provided
    categories = None
    if args.categories:
        categories = [cat.strip().lower() for cat in args.categories.split(',') if cat.strip()]
        if not categories:
            print("❌ Invalid categories format. Use comma-separated values like: restaurant,cafe,bar")
            sys.exit(1)
    
    try:
        # Handle different actions
        if args.health:
            print("🔍 Running health check...")
            success = await test_health_check()
            sys.exit(0 if success else 1)
            
        elif args.text:
            success = await search_by_text(
                query=args.text,
                categories=categories,
                max_results=min(args.max_results, 20)
            )
            sys.exit(0 if success else 1)
            
        elif args.zip:
            if not categories:
                print("❌ Zip code search requires --categories argument")
                print("Example: python places.py --zip 90210 --categories restaurant,cafe")
                print("Use --list-types to see available categories")
                sys.exit(1)
                
            # Validate zip code format
            if not args.zip.isdigit() or len(args.zip) not in [5, 9]:
                print("❌ Invalid zip code format. Use 5-digit (90210) or 9-digit format")
                sys.exit(1)
                
            success = await search_by_zip(
                zip_code=args.zip,
                categories=categories,
                radius=args.radius,
                max_results=min(args.max_results, 20)
            )
            sys.exit(0 if success else 1)
            
        elif args.list_types:
            display_place_types()
            sys.exit(0)
            
        else:
            # No arguments provided, run test suite
            await main()
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run all tests
        asyncio.run(main())
    else:
        asyncio.run(main_cli())
