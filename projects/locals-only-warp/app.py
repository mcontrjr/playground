import os
import json
import logging
from typing import List, Dict, Any
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
import time
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not GOOGLE_MAPS_API_KEY:
    logger.warning("⚠️ GOOGLE_MAPS_API_KEY not found in environment variables")

# Initialize LangChain with Anthropic for AI enhancement
try:
    llm = ChatAnthropic(
        model="claude-3-haiku-20240307",
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
        temperature=0.3,
        max_tokens=1500
    )
    logger.info("✅ LangChain Anthropic initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize LangChain Anthropic: {e}")
    llm = None

class GooglePlacesService:
    """Service for Google Places API integration"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.places_base_url = "https://maps.googleapis.com/maps/api/place"
        self.geocoding_base_url = "https://maps.googleapis.com/maps/api/geocode"

    def get_location_from_zip(self, zip_code: str) -> Dict[str, Any]:
        """Get location details from zip code using Google Geocoding API"""
        try:
            url = f"{self.geocoding_base_url}/json"
            params = {
                'address': zip_code,
                'key': self.api_key,
                'components': 'country:US'
            }

            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']

                # Extract address components
                city = ""
                state = ""
                for component in result['address_components']:
                    types = component['types']
                    if 'locality' in types:
                        city = component['long_name']
                    elif 'administrative_area_level_1' in types:
                        state = component['short_name']

                return {
                    'success': True,
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'city': city,
                    'state': state,
                    'zip_code': zip_code,
                    'formatted_address': result['formatted_address']
                }
            else:
                return {
                    'success': False,
                    'error': 'Location not found'
                }
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_nearby_places(self, latitude: float, longitude: float, category: str, radius: int = 8000) -> Dict[str, Any]:
        """Search for nearby places using Google Places API"""
        try:
            # Updated mapping: outdoors combines hiking and beaches
            place_type_mapping = {
                'restaurants': {'type': 'restaurant', 'keyword': 'local'},
                'coffee': {'type': 'cafe', 'keyword': 'coffee'},
                'thrift': {'type': 'store', 'keyword': 'thrift second hand consignment'},
                'nightlife': {'type': 'bar', 'keyword': 'bar club nightlife'},
                'outdoors': {'type': 'hiking_area', 'keyword': 'hiking outdoor recreation'},
                'shopping': {'type': 'shopping_mall', 'keyword': None}
            }

            mapping = place_type_mapping.get(category, {'type': 'establishment', 'keyword': None})
            place_type = mapping['type']
            keyword = mapping['keyword']

            url = f"{self.places_base_url}/nearbysearch/json"
            params = {
                'location': f"{latitude},{longitude}",
                'radius': radius,
                'type': place_type,
                'key': self.api_key,
                'opennow': False
            }

            if keyword:
                params['keyword'] = keyword

            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == 'OK':
                places = []
                for place in data.get('results', [])[:20]:  # Limit to 20 results
                    place_info = {
                        'name': place.get('name', ''),
                        'type': place.get('types', ['establishment'])[0].replace('_', ' ').title(),
                        'rating': place.get('rating', 0),
                        'price_level': place.get('price_level', 0),
                        'latitude': place['geometry']['location']['lat'],
                        'longitude': place['geometry']['location']['lng'],
                        'address': place.get('vicinity', ''),
                        'place_id': place.get('place_id', ''),
                        'photo_reference': place.get('photos', [{}])[0].get('photo_reference', '') if place.get('photos') else '',
                        'source': 'google_places'
                    }
                    places.append(place_info)

                return {
                    'success': True,
                    'places': places,
                    'total_count': len(places)
                }
            else:
                return {
                    'success': False,
                    'error': f"Google Places API error: {data.get('status')}"
                }
        except Exception as e:
            logger.error(f"Places search error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Initialize Google Places service
google_places = GooglePlacesService(GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None

class RecommendationService:
    """Recommendation service using Google Places API with AI enhancement"""

    def __init__(self, google_places, llm):
        self.google_places = google_places
        self.llm = llm

    def generate_recommendations(self, zip_code: str, category: str = "restaurants") -> Dict[str, Any]:
        """Generate recommendations using Google Places API"""

        if not self.google_places:
            return {
                'success': False,
                'error': 'Google Places API is not available - missing API key'
            }

        try:
            logger.info(f"🎯 Processing request with Google Places API: {zip_code}, {category}")

            # Get location from zip code
            location_result = self.google_places.get_location_from_zip(zip_code)

            if not location_result['success']:
                return location_result

            # Search for nearby places
            places_result = self.google_places.search_nearby_places(
                location_result['latitude'],
                location_result['longitude'],
                category
            )

            if not places_result['success']:
                return places_result

            recommendations = places_result['places']

            # Enhance with AI insights if available
            if self.llm and recommendations:
                enhanced_recommendations = self._enhance_with_ai(
                    recommendations,
                    location_result,
                    category
                )
                recommendations = enhanced_recommendations

            return {
                'success': True,
                'recommendations': recommendations,
                'location': {
                    'city': location_result['city'],
                    'state': location_result['state'],
                    'zip_code': zip_code,
                    'latitude': location_result['latitude'],
                    'longitude': location_result['longitude'],
                    'formatted_address': location_result['formatted_address']
                },
                'total_count': len(recommendations),
                'service_type': 'google_places_enhanced',
                'api_sources': ['google_places', 'google_geocoding']
            }

        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {e}")
            return {
                'success': False,
                'error': f'Service error: {str(e)}'
            }

    def _enhance_with_ai(self, recommendations: List[Dict], location: Dict, category: str) -> List[Dict]:
        """Use AI to add local insights to Google Places data"""
        try:
            city = location.get('city', 'Unknown City')
            state = location.get('state', 'Unknown State')
            zip_code = location.get('zip_code', '')

            # Create summary of places for AI
            places_summary = "\n".join([
                f"- {rec['name']}: {rec['rating']} stars, {rec['type']}, "
                f"Address: {rec['address']}"
                for rec in recommendations[:6]
            ])

            system_prompt = f"""You are a local expert for {city}, {state} (ZIP: {zip_code}). I have real business data from Google Places API with verified locations.

Your job:
1. Keep ALL factual data (names, ratings, addresses) EXACTLY as provided
2. Add authentic local insights about what makes each place special
3. Explain why locals would choose these specific locations
4. Add helpful descriptions and recommendation reasons"""

            user_prompt = f"""Here are real businesses from Google Places in {city}, {state} ({zip_code}) for {category}:

{places_summary}

Enhance each business with local insights while keeping all factual data exact. Return JSON array:
[
  {{
    "name": "exact business name",
    "type": "exact business type",
    "description": "enhanced with local insights",
    "address": "exact address",
    "recommendation_reason": "authentic local perspective",
    "rating": exact_rating,
    "price_level": exact_price_level,
    "latitude": exact_latitude,
    "longitude": exact_longitude,
    "place_id": "exact_place_id",
    "photo_reference": "exact_photo_reference",
    "source": "google_places_enhanced"
  }}
]"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)

            # Parse AI response
            try:
                ai_content = response.content
                if '```json' in ai_content:
                    ai_content = ai_content.split('```json')[1].split('```')[0].strip()
                elif '```' in ai_content:
                    ai_content = ai_content.split('```')[1].split('```')[0].strip()

                enhanced = json.loads(ai_content)

                if isinstance(enhanced, list) and len(enhanced) > 0:
                    logger.info(f"✅ AI enhanced {len(enhanced)} Google Places recommendations")
                    return enhanced

            except Exception as parse_error:
                logger.warning(f"⚠️ AI parsing failed, using original Google Places data: {parse_error}")

            # Fallback: return original data with basic enhancements
            for rec in recommendations:
                rec['description'] = f"Popular {rec['type'].lower()} in {city}"
                rec['recommendation_reason'] = f"Well-rated local spot in {zip_code}"
                rec['source'] = 'google_places'

            return recommendations

        except Exception as e:
            logger.error(f"❌ AI enhancement failed: {e}")
            return recommendations

# Initialize recommendation service
if google_places:
    recommendation_service = RecommendationService(google_places, llm)
    logger.info("✅ Recommendation service with Google Places API initialized")
else:
    recommendation_service = None
    logger.error("❌ Cannot initialize service - missing Google Maps API key")

@app.route('/')
def index():
    """Landing page - always show if user hasn't been through onboarding"""
    if not session.get('onboarding_complete'):
        return render_template('pages/landing.html')
    elif session.get('user_location'):
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('onboarding'))

@app.route('/onboarding')
def onboarding():
    """Onboarding flow"""
    return render_template('pages/onboarding.html', google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/dashboard')
def dashboard():
    """Main dashboard - requires location"""
    if not session.get('user_location'):
        return redirect(url_for('onboarding'))

    user_location = session.get('user_location', {})
    return render_template('pages/dashboard.html',
                         user_location=user_location,
                         google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/change-location')
def change_location():
    """Change location without going through landing page"""
    # Keep onboarding_complete but reset location
    session.pop('user_location', None)
    return redirect(url_for('onboarding'))

@app.route('/api/set-location', methods=['POST'])
def set_location():
    """Set user location from onboarding"""
    try:
        data = request.get_json()
        session['user_location'] = {
            'zip_code': data.get('zip_code'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'city': data.get('city'),
            'state': data.get('state'),
            'formatted_address': data.get('formatted_address')
        }
        session['onboarding_complete'] = True

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error setting location: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-preferences', methods=['POST'])
def update_preferences():
    """Update user category preferences"""
    try:
        data = request.get_json()
        starred_categories = data.get('starred_categories', [])

        # Validate categories
        valid_categories = ['restaurants', 'coffee', 'thrift', 'nightlife', 'outdoors', 'shopping']
        starred_categories = [cat for cat in starred_categories if cat in valid_categories]

        session['starred_categories'] = starred_categories

        return jsonify({'success': True, 'starred_categories': starred_categories})
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-preferences', methods=['GET'])
def get_preferences():
    """Get user category preferences"""
    try:
        starred_categories = session.get('starred_categories', [])
        return jsonify({'success': True, 'starred_categories': starred_categories})
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """API endpoint for getting recommendations from Google Places"""

    if not recommendation_service:
        return jsonify({
            'success': False,
            'error': 'Google Places API service is not available - missing API key'
        }), 503

    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        zip_code = data.get('zip_code', '').strip()
        category = data.get('category', 'restaurants').strip()

        if not zip_code:
            # Try to use session location
            user_location = session.get('user_location', {})
            zip_code = user_location.get('zip_code', '')

        if not zip_code:
            return jsonify({'success': False, 'error': 'Zip code is required'}), 400

        # Validate US zip code format
        zip_clean = zip_code.replace('-', '').replace(' ', '')
        if not (zip_clean.isdigit() and (len(zip_clean) == 5 or len(zip_clean) == 9)):
            return jsonify({
                'success': False,
                'error': 'Please enter a valid US zip code (e.g., 12345 or 12345-6789)'
            }), 400

        # Validate category - updated to include outdoors
        valid_categories = ['restaurants', 'coffee', 'thrift', 'nightlife', 'outdoors', 'shopping']
        if category not in valid_categories:
            category = 'restaurants'

        logger.info(f"🚀 Processing request with Google Places API: {zip_code}, {category}")

        # Get recommendations using Google Places
        result = recommendation_service.generate_recommendations(zip_code, category)

        if result['success']:
            count = result.get('total_count', 0)
            logger.info(f"✅ SUCCESS: Generated {count} recommendations from Google Places")
            return jsonify(result)
        else:
            logger.warning(f"⚠️ Google Places recommendation failed: {result.get('error')}")
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"❌ API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Service error. Please try again.'
        }), 500

@app.route('/api/photo')
def get_photo():
    """Proxy for Google Places photos"""
    photo_reference = request.args.get('photo_reference')
    max_width = request.args.get('maxwidth', 400)

    if not photo_reference or not GOOGLE_MAPS_API_KEY:
        return '', 404

    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"
    return redirect(photo_url)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    health_status = {
        'status': 'healthy',
        'service': 'locals-only-enhanced',
        'timestamp': time.time(),
        'components': {
            'google_places_api': google_places is not None,
            'google_maps_api_key': GOOGLE_MAPS_API_KEY is not None,
            'llm': llm is not None,
            'recommendation_service': recommendation_service is not None
        },
        'features': {
            'google_places_integration': True,
            'google_maps_embed': True,
            'location_services': True,
            'ai_enhancement': llm is not None,
            'onboarding_flow': True,
            'dashboard_view': True,
            'categories': ['restaurants', 'coffee', 'thrift', 'nightlife', 'outdoors', 'shopping']
        }
    }

    # Check if core components are healthy
    core_healthy = all([
        health_status['components']['google_places_api'],
        health_status['components']['google_maps_api_key']
    ])

    if core_healthy:
        return jsonify(health_status)
    else:
        health_status['status'] = 'degraded'
        return jsonify(health_status), 503

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Locals Only app with Google Places API...")
    logger.info("🗺️ Features: Google Maps, Places API, Onboarding, Dashboard")
    logger.info("🏷️ Categories: Restaurants, Coffee, Thrift, Nightlife, Outdoors, Shopping")
    app.run(debug=True, host='0.0.0.0', port=5005)
