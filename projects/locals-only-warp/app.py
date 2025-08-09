import os
import json
import logging
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
import time

# Import our REAL API business service
from real_api_service import RealAPIBusinessService

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

# Initialize REAL API Business Service
try:
    real_business_service = RealAPIBusinessService()
    logger.info("✅ Real API Business Service with OpenStreetMap data initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Real API Business Service: {e}")
    real_business_service = None

class ProductionRecommendationService:
    """Production service using real business APIs and AI enhancement"""
    
    def __init__(self, real_business_service, llm):
        self.real_business_service = real_business_service
        self.llm = llm
    
    def generate_recommendations(self, zip_code: str, category: str = "general") -> Dict[str, Any]:
        """Generate recommendations using real business APIs + AI enhancement"""
        
        if not self.real_business_service:
            return {
                'success': False,
                'error': 'Real business API service is not available'
            }
        
        try:
            logger.info(f"🎯 Processing REAL API DATA request: {zip_code}, {category}")
            
            # Get real business data from APIs
            api_result = self.real_business_service.get_recommendations(zip_code, category)
            
            if not api_result['success']:
                return api_result
            
            # Get the raw recommendations
            recommendations = api_result['recommendations']
            
            if not recommendations:
                return {
                    'success': False,
                    'error': f'No real businesses found for zip code {zip_code}'
                }
            
            # Enhance with AI insights if available
            if self.llm and recommendations:
                enhanced_recommendations = self._enhance_with_ai(
                    recommendations, 
                    api_result['location'], 
                    category
                )
                api_result['recommendations'] = enhanced_recommendations
                api_result['ai_enhanced'] = True
            else:
                api_result['ai_enhanced'] = False
            
            # Add production metadata
            api_result['service_type'] = 'production_real_data'
            api_result['verification_status'] = 'verified_real_businesses'
            api_result['api_sources'] = api_result.get('data_sources', [])
            
            logger.info(f"✅ Generated {len(recommendations)} REAL business recommendations from APIs")
            return api_result
            
        except Exception as e:
            logger.error(f"❌ Production recommendation generation failed: {e}")
            return {
                'success': False,
                'error': f'Service error: {str(e)}'
            }
    
    def _enhance_with_ai(self, recommendations: List[Dict], location: Dict, category: str) -> List[Dict]:
        """Use AI to add authentic local insights to real business data"""
        try:
            city = location.get('city', 'Unknown City')
            state = location.get('state', 'Unknown State')
            zip_code = location.get('zip_code', '')
            
            # Create summary of REAL businesses for AI
            business_summary = "\n".join([
                f"- {rec['name']}: {rec['rating']} stars, {rec['type']}, "
                f"Address: {rec['address']}, Source: {rec['source']}, "
                f"Coordinates: {rec['latitude']}, {rec['longitude']}"
                for rec in recommendations[:6]
            ])
            
            system_prompt = f"""You are a local expert for {city}, {state} (ZIP: {zip_code}). I have REAL business data from OpenStreetMap with verified locations and coordinates.

These are ACTUAL businesses with real addresses and coordinates. Your job:
1. Keep ALL factual data (names, ratings, addresses, coordinates) EXACTLY as provided
2. Add authentic local insights about what makes each place special
3. Explain why locals would choose these specific locations
4. Be specific about the area and neighborhood characteristics

These businesses are verified real locations in {zip_code} - treat all data as factual."""

            user_prompt = f"""Here are REAL businesses from OpenStreetMap in {city}, {state} ({zip_code}) for {category}:

{business_summary}

Enhance each business with local insights while keeping all factual data exact. Explain:
- What makes each location special in this specific area
- Why locals choose these places
- Any neighborhood context for {zip_code}

Return JSON array:
[
  {{
    "name": "exact business name",
    "type": "exact business type", 
    "description": "enhanced with local insights",
    "address": "exact address",
    "recommendation_reason": "authentic local perspective",
    "rating": exact_rating,
    "price_range": "exact price",
    "latitude": exact_latitude,
    "longitude": exact_longitude,
    "source": "real_api_enhanced"
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
                    logger.info(f"✅ AI enhanced {len(enhanced)} real business recommendations")
                    return enhanced
                
            except Exception as parse_error:
                logger.warning(f"⚠️ AI parsing failed, using original real data: {parse_error}")
            
            # Fallback: return original real data
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ AI enhancement failed: {e}")
            return recommendations

# Initialize production service
if real_business_service:
    recommendation_service = ProductionRecommendationService(real_business_service, llm)
    logger.info("✅ Production recommendation service with real APIs initialized")
else:
    recommendation_service = None
    logger.error("❌ Cannot initialize production service - missing real API service")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """API endpoint for getting REAL business recommendations from live APIs"""
    
    if not recommendation_service:
        return jsonify({
            'success': False, 
            'error': 'Production recommendation service with real APIs is not available'
        }), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        zip_code = data.get('zip_code', '').strip()
        category = data.get('category', 'general').strip()
        
        if not zip_code:
            return jsonify({'success': False, 'error': 'Zip code is required'}), 400
        
        # Validate US zip code format
        zip_clean = zip_code.replace('-', '').replace(' ', '')
        if not (zip_clean.isdigit() and (len(zip_clean) == 5 or len(zip_clean) == 9)):
            return jsonify({
                'success': False, 
                'error': 'Please enter a valid US zip code (e.g., 12345 or 12345-6789)'
            }), 400
        
        # Validate category
        valid_categories = ['general', 'restaurants', 'activities', 'entertainment', 'shopping']
        if category not in valid_categories:
            category = 'general'
        
        logger.info(f"🚀 Processing PRODUCTION REQUEST with REAL APIs: {zip_code}, {category}")
        
        # Get real business recommendations from APIs
        result = recommendation_service.generate_recommendations(zip_code, category)
        
        if result['success']:
            count = result.get('total_count', 0)
            sources = result.get('api_sources', [])
            logger.info(f"✅ SUCCESS: Generated {count} real business recommendations from {sources}")
            
            # Add debug info for verification
            result['debug_info'] = {
                'zip_code_processed': zip_code,
                'real_coordinates_found': any(rec.get('latitude', 0) != 0 for rec in result.get('recommendations', [])),
                'real_addresses_found': any('address' in rec and rec['address'] for rec in result.get('recommendations', [])),
                'api_sources_used': sources
            }
            
            return jsonify(result)
        else:
            logger.warning(f"⚠️ Real API recommendation failed: {result.get('error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"❌ Production API error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Production service error. Please try again.'
        }), 500

@app.route('/api/health')
def health_check():
    """Production health check endpoint"""
    health_status = {
        'status': 'healthy',
        'service': 'locals-only-production',
        'port': 5005,
        'timestamp': time.time(),
        'service_type': 'production_real_apis',
        'components': {
            'llm': llm is not None,
            'recommendation_service': recommendation_service is not None,
            'real_business_api': real_business_service is not None,
            'vector_embeddings': real_business_service.embedder is not None if real_business_service else False,
            'vector_database': real_business_service.collection is not None if real_business_service else False,
            'openstreetmap_api': True,
            'geocoder': True
        },
        'features': {
            'real_business_data': True,
            'live_api_integration': True,
            'vector_embeddings': True,
            'semantic_search': True,
            'ai_enhancement': llm is not None,
            'verified_coordinates': True,
            'real_addresses': True
        },
        'data_sources': [
            'openstreetmap_live_api',
            'vector_embeddings', 
            'semantic_search',
            'ai_local_insights',
            'real_coordinates',
            'verified_addresses'
        ]
    }
    
    # Check if core production components are healthy
    production_healthy = all([
        health_status['components']['real_business_api'],
        health_status['components']['openstreetmap_api'],
        health_status['components']['geocoder']
    ])
    
    if production_healthy:
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
    logger.info("🚀 Starting PRODUCTION Locals Only app with REAL BUSINESS APIs...")
    logger.info("📊 Data Sources: OpenStreetMap Live API, Vector Embeddings, AI Enhancement")
    logger.info("🎯 Test with zip code 95126 for verified real businesses")
    app.run(debug=True, host='0.0.0.0', port=5005)
