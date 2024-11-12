from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from main_test_v7_api1 import send_message, character_build, main_async
import concurrent.futures
import logging
from functools import partial

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a ThreadPoolExecutor for running async code
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def run_async(coro):
    """Helper function to run async code in the thread pool."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get('user_id')
        user_first_name = data.get('user_first_name')
        char_name = data.get('char_name')
        message = data.get('message')

        # Validate input
        if not all([user_id, user_first_name, char_name, message]):
            return jsonify({
                'error': 'Missing required fields'
            }), 400

        # Get or create character instance
        char = character_build(char_name)
        if not char:
            return jsonify({
                'error': f'Character {char_name} not found'
            }), 404

        # Run the async chat function in the thread pool
        future = thread_pool.submit(
            run_async,
            send_message(
                message=message,
                user_id=user_id,
                user_first_name=user_first_name,
                char_name=char_name,
                char=char
            )
        )
        
        # Get the response
        response, image_intent = future.result()

        return jsonify({
            'response': response,
            'image_intent': image_intent
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

# Create the Flask application
flask_app = app

if __name__ == '__main__':
    # Run the Flask app
    flask_app.run(host='0.0.0.0', port=5000, threaded=True) 