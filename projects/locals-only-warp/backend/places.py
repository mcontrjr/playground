#!/usr/bin/env python3
"""
Standalone utility script for testing Google Places API integration.
This script can be run independently to test the backend functionality.

Example usage:
  python places.py --test all
  python places.py --nearby --location "-33.8688,151.2093" --radius 1500 --type restaurant
  python places.py --text-search --query "pizza in Sydney" --location "-33.8688,151.2093"
  python places.py --health
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.places_client import GooglePlacesClient, GooglePlacesAPIError
from models import NearbySearchRequest, TextSearchRequest, RankBy, PriceLevel


async def test_nearby_search():
    """Test nearby search functionality."""
    print("\n=== Testing Nearby Search ===")
    
    # Example: Search for restaurants near Sydney Harbour
    request = NearbySearchRequest(
        location="-33.8670522,151.1957362",  # Sydney Harbour coordinates
        radius=1500,
        type="restaurant",
        keyword="cruise"
    )
    
    try:
        async with GooglePlacesClient() as client:
            response = await client.nearby_search(request)
            
        print(f"Status: {response.status}")
        print(f"Found {len(response.results)} places")
        
        # Display first few results
        for i, place in enumerate(response.results[:3], 1):
            print(f"\n{i}. {place.name}")
            if place.formatted_address:
                print(f"   Address: {place.formatted_address}")
            if place.rating:
                print(f"   Rating: {place.rating} ({place.user_ratings_total} reviews)")
            if place.price_level:
                print(f"   Price Level: {place.price_level}")
            if place.types:
                print(f"   Types: {', '.join(place.types[:3])}")
        
        return True
        
    except GooglePlacesAPIError as e:
        print(f"API Error: {e.detail}")
        if hasattr(e, 'places_status'):
            print(f"Places API Status: {e.places_status}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


async def test_text_search():
    """Test text search functionality."""
    print("\n=== Testing Text Search ===")
    
    # Example: Search for pizza places in Sydney
    request = TextSearchRequest(
        query="pizza restaurants in Sydney",
        location="-33.8688,151.2093",  # Sydney city center
        radius=5000
    )
    
    try:
        async with GooglePlacesClient() as client:
            response = await client.text_search(request)
            
        print(f"Status: {response.status}")
        print(f"Found {len(response.results)} places")
        
        # Display first few results
        for i, place in enumerate(response.results[:3], 1):
            print(f"\n{i}. {place.name}")
            if place.formatted_address:
                print(f"   Address: {place.formatted_address}")
            if place.rating:
                print(f"   Rating: {place.rating} ({place.user_ratings_total} reviews)")
            if place.business_status:
                print(f"   Status: {place.business_status}")
        
        return True
        
    except GooglePlacesAPIError as e:
        print(f"API Error: {e.detail}")
        if hasattr(e, 'places_status'):
            print(f"Places API Status: {e.places_status}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


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


async def test_distance_ranking():
    """Test distance-based ranking."""
    print("\n=== Testing Distance Ranking ===")
    
    # Example: Find nearby cafes ranked by distance
    request = NearbySearchRequest(
        location="-33.8688,151.2093",  # Sydney city center
        rankby=RankBy.DISTANCE,
        type="cafe",
        keyword="coffee"
    )
    
    try:
        async with GooglePlacesClient() as client:
            response = await client.nearby_search(request)
            
        print(f"Status: {response.status}")
        print(f"Found {len(response.results)} places (ranked by distance)")
        
        # Display first few results
        for i, place in enumerate(response.results[:3], 1):
            print(f"\n{i}. {place.name}")
            if place.vicinity:
                print(f"   Vicinity: {place.vicinity}")
            if place.rating:
                print(f"   Rating: {place.rating}")
            if place.opening_hours and hasattr(place.opening_hours, 'open_now'):
                status = "Open" if place.opening_hours.open_now else "Closed"
                print(f"   Status: {status}")
        
        return True
        
    except GooglePlacesAPIError as e:
        print(f"API Error: {e.detail}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


async def custom_nearby_search(args):
    """Perform a custom nearby search with user-provided parameters."""
    print("\n=== Custom Nearby Search ===")
    
    try:
        # Build request from arguments
        request_params = {
            'location': args.location,
        }
        
        if args.radius:
            request_params['radius'] = args.radius
            request_params['rankby'] = RankBy.PROMINENCE
        elif args.rankby == 'distance':
            request_params['rankby'] = RankBy.DISTANCE
        else:
            request_params['rankby'] = RankBy.PROMINENCE
            if not args.radius:
                request_params['radius'] = 1500  # Default radius
        
        if args.keyword:
            request_params['keyword'] = args.keyword
        if args.name:
            request_params['name'] = args.name
        if args.type:
            request_params['type'] = args.type
        if args.language:
            request_params['language'] = args.language
        if args.minprice:
            request_params['minprice'] = PriceLevel(args.minprice)
        if args.maxprice:
            request_params['maxprice'] = PriceLevel(args.maxprice)
        if args.opennow is not None:
            request_params['opennow'] = args.opennow
        if args.pagetoken:
            request_params['pagetoken'] = args.pagetoken
        
        request = NearbySearchRequest(**request_params)
        
        async with GooglePlacesClient() as client:
            response = await client.nearby_search(request)
            
        print(f"Status: {response.status}")
        print(f"Found {len(response.results)} places")
        
        if args.json:
            # Output JSON format
            results_data = []
            for place in response.results[:args.limit]:
                place_data = {
                    'name': place.name,
                    'place_id': place.place_id,
                    'formatted_address': place.formatted_address,
                    'vicinity': place.vicinity,
                    'rating': place.rating,
                    'user_ratings_total': place.user_ratings_total,
                    'price_level': place.price_level,
                    'types': place.types,
                    'business_status': place.business_status,
                }
                if place.geometry:
                    place_data['location'] = {
                        'lat': place.geometry.location.lat,
                        'lng': place.geometry.location.lng
                    }
                results_data.append(place_data)
            
            print("\nJSON Output:")
            print(json.dumps(results_data, indent=2))
        else:
            # Human-readable format
            for i, place in enumerate(response.results[:args.limit], 1):
                print(f"\n{i}. {place.name}")
                if place.place_id:
                    print(f"   Place ID: {place.place_id}")
                if place.formatted_address:
                    print(f"   Address: {place.formatted_address}")
                elif place.vicinity:
                    print(f"   Vicinity: {place.vicinity}")
                if place.rating:
                    print(f"   Rating: {place.rating} ({place.user_ratings_total} reviews)")
                if place.price_level is not None:
                    price_labels = {0: "Free", 1: "Inexpensive", 2: "Moderate", 3: "Expensive", 4: "Very Expensive"}
                    print(f"   Price Level: {place.price_level} ({price_labels.get(place.price_level, 'Unknown')})")
                if place.types:
                    print(f"   Types: {', '.join(place.types[:5])}")
                if place.business_status:
                    print(f"   Status: {place.business_status}")
                if place.geometry:
                    print(f"   Location: {place.geometry.location.lat}, {place.geometry.location.lng}")
        
        if response.next_page_token:
            print(f"\n📄 Next page token: {response.next_page_token}")
            print("Use --pagetoken to get more results")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def custom_text_search(args):
    """Perform a custom text search with user-provided parameters."""
    print("\n=== Custom Text Search ===")
    
    try:
        # Build request from arguments
        request_params = {
            'query': args.query,
        }
        
        if args.location:
            request_params['location'] = args.location
        if args.radius:
            request_params['radius'] = args.radius
        if args.language:
            request_params['language'] = args.language
        if args.minprice:
            request_params['minprice'] = PriceLevel(args.minprice)
        if args.maxprice:
            request_params['maxprice'] = PriceLevel(args.maxprice)
        if args.opennow is not None:
            request_params['opennow'] = args.opennow
        if args.pagetoken:
            request_params['pagetoken'] = args.pagetoken
        if args.type:
            request_params['type'] = args.type
        if args.region:
            request_params['region'] = args.region
        
        request = TextSearchRequest(**request_params)
        
        async with GooglePlacesClient() as client:
            response = await client.text_search(request)
            
        print(f"Status: {response.status}")
        print(f"Found {len(response.results)} places")
        
        if args.json:
            # Output JSON format
            results_data = []
            for place in response.results[:args.limit]:
                place_data = {
                    'name': place.name,
                    'place_id': place.place_id,
                    'formatted_address': place.formatted_address,
                    'rating': place.rating,
                    'user_ratings_total': place.user_ratings_total,
                    'price_level': place.price_level,
                    'types': place.types,
                    'business_status': place.business_status,
                }
                if place.geometry:
                    place_data['location'] = {
                        'lat': place.geometry.location.lat,
                        'lng': place.geometry.location.lng
                    }
                results_data.append(place_data)
            
            print("\nJSON Output:")
            print(json.dumps(results_data, indent=2))
        else:
            # Human-readable format
            for i, place in enumerate(response.results[:args.limit], 1):
                print(f"\n{i}. {place.name}")
                if place.place_id:
                    print(f"   Place ID: {place.place_id}")
                if place.formatted_address:
                    print(f"   Address: {place.formatted_address}")
                if place.rating:
                    print(f"   Rating: {place.rating} ({place.user_ratings_total} reviews)")
                if place.price_level is not None:
                    price_labels = {0: "Free", 1: "Inexpensive", 2: "Moderate", 3: "Expensive", 4: "Very Expensive"}
                    print(f"   Price Level: {place.price_level} ({price_labels.get(place.price_level, 'Unknown')})")
                if place.types:
                    print(f"   Types: {', '.join(place.types[:5])}")
                if place.business_status:
                    print(f"   Status: {place.business_status}")
                if place.geometry:
                    print(f"   Location: {place.geometry.location.lat}, {place.geometry.location.lng}")
        
        if response.next_page_token:
            print(f"\n📄 Next page token: {response.next_page_token}")
            print("Use --pagetoken to get more results")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def custom_health_check(args):
    """Perform a health check."""
    return await test_health_check()


async def run_all_tests():
    """Run the full test suite."""
    return await main()


async def main():
    """Run all tests."""
    print("Google Places API Backend Test Suite")
    print("=====================================")
    
    tests = [
        ("Health Check", test_health_check),
        ("Nearby Search", test_nearby_search),
        ("Text Search", test_text_search),
        ("Distance Ranking", test_distance_ranking),
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


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Google Places API testing and utility script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python places.py --test all
  
  # Test specific functionality
  python places.py --health
  
  # Nearby search with custom parameters
  python places.py --nearby --location "-33.8688,151.2093" --radius 1500 --type restaurant
  
  # Nearby search by distance ranking
  python places.py --nearby --location "-33.8688,151.2093" --rankby distance --type cafe --keyword coffee
  
  # Text search
  python places.py --text-search --query "pizza in Sydney" --location "-33.8688,151.2093" --radius 5000
  
  # Get results in JSON format
  python places.py --nearby --location "-33.8688,151.2093" --radius 2000 --type restaurant --json --limit 5
  
  # Use page token for more results
  python places.py --nearby --location "-33.8688,151.2093" --radius 1500 --pagetoken "YOUR_TOKEN"
        """
    )
    
    # Main action groups
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--test', choices=['all'], help='Run test suite')
    action_group.add_argument('--health', action='store_true', help='Run health check only')
    action_group.add_argument('--nearby', action='store_true', help='Perform nearby search')
    action_group.add_argument('--text-search', action='store_true', help='Perform text search')
    
    # Common parameters
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of results (default: 10)')
    parser.add_argument('--language', help='Language code (e.g., en, es, fr)')
    parser.add_argument('--pagetoken', help='Page token for additional results')
    
    # Location parameters
    parser.add_argument('--location', help='Location as lat,lng (required for nearby and optional for text search)')
    parser.add_argument('--radius', type=int, help='Search radius in meters (1-50000)')
    
    # Search parameters
    parser.add_argument('--keyword', help='Keyword to match')
    parser.add_argument('--name', help='Name to match (nearby search only)')
    parser.add_argument('--type', help='Place type (e.g., restaurant, cafe, hospital)')
    parser.add_argument('--query', help='Text query (required for text search)')
    parser.add_argument('--region', help='Country/region code for biasing results (text search only)')
    
    # Ranking and filtering
    parser.add_argument('--rankby', choices=['prominence', 'distance'], default='prominence',
                       help='Ranking method for nearby search (default: prominence)')
    parser.add_argument('--minprice', choices=['0', '1', '2', '3', '4'],
                       help='Minimum price level (0=Free, 1=Inexpensive, 2=Moderate, 3=Expensive, 4=Very Expensive)')
    parser.add_argument('--maxprice', choices=['0', '1', '2', '3', '4'],
                       help='Maximum price level (0=Free, 1=Inexpensive, 2=Moderate, 3=Expensive, 4=Very Expensive)')
    parser.add_argument('--opennow', action='store_true', help='Only return places that are open now')
    parser.add_argument('--not-opennow', dest='opennow', action='store_false', help='Include places regardless of open status')
    
    return parser


async def main_cli():
    """Main CLI function."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Validate arguments
        if args.nearby:
            if not args.location:
                parser.error("--nearby requires --location")
            if args.rankby == 'distance' and args.radius:
                parser.error("--radius cannot be used with --rankby distance")
            elif args.rankby == 'prominence' and not args.radius:
                print("⚠️  No radius specified, using default radius of 1500 meters")
        
        if args.text_search:
            if not args.query:
                parser.error("--text-search requires --query")
        
        if args.radius and (args.radius < 1 or args.radius > 50000):
            parser.error("--radius must be between 1 and 50000 meters")
        
        # Execute based on arguments
        if args.test == 'all':
            await main()
        elif args.health:
            success = await custom_health_check(args)
            sys.exit(0 if success else 1)
        elif args.nearby:
            success = await custom_nearby_search(args)
            sys.exit(0 if success else 1)
        elif args.text_search:
            success = await custom_text_search(args)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # If no arguments provided, run the full test suite
    if len(sys.argv) == 1:
        asyncio.run(main())
    else:
        asyncio.run(main_cli())
