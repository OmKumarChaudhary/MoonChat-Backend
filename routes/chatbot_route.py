from flask import Blueprint, jsonify, request
from chatbot.chat import get_response

# Create a Blueprint for chatbot-related routes
chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/ask', methods=['POST'])
def ask_chatbot():
    """
    Receives a message from the user and returns an AI-generated response.
    """
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message']
    
    try:
        response = get_response(user_message)
        return jsonify({
            'response': response,
            'status': 'success'
        }), 200
    except Exception as e:
        import traceback
        error_msg = f"Error in chatbot response: {e}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'status': 'error',
            'details': 'Please check server logs for more info'
        }), 500

@chatbot_bp.route('/status', methods=['GET'])
def chatbot_status():
    """Check if the chatbot service is active."""
    return jsonify({'status': 'online', 'message': 'MoonChat AI Assistant is ready'}), 200
