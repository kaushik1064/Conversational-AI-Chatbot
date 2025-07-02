from flask import Flask, request, jsonify, render_template
from utils.search_and_scrape import search_and_scrape
from utils.vector_store import create_vector_store
from groq import Groq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# Store multiple chat sessions
chat_sessions = {}

class ChatSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.memory = ConversationBufferMemory(memory_key="history", return_messages=True)
        self.vectorstore = None
        self.created_at = datetime.now()
        self.last_used = datetime.now()
    
    def update_last_used(self):
        self.last_used = datetime.now()

def get_or_create_session(session_id=None):
    """Get existing session or create new one"""
    if session_id and session_id in chat_sessions:
        session = chat_sessions[session_id]
        session.update_last_used()
        return session
    else:
        # Create new session
        new_session_id = str(uuid.uuid4())
        new_session = ChatSession(new_session_id)
        chat_sessions[new_session_id] = new_session
        return new_session

def check_topic_relevance(user_query, context, threshold=0.3):
    """Check if the user query is relevant to the existing context using Groq"""
    
    try:
        relevance_check = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a topic relevance checker. Your job is to determine if a user query is related to the provided context.

Respond with only one word:
- "RELEVANT" if the query is related to the context topic
- "IRRELEVANT" if the query is about a completely different topic

Be strict - only mark as RELEVANT if there's a clear topical connection."""
                },
                {
                    "role": "user",
                    "content": f"Context: {context[:500]}...\n\nUser Query: {user_query}\n\nIs this query relevant to the context?"
                }
            ],
            model="llama3-8b-8192",
            temperature=0.1,
            max_tokens=10
        )
        
        response = relevance_check.choices[0].message.content.strip().upper()
        return "RELEVANT" in response
        
    except Exception as e:
        print(f"Error checking relevance: {e}")
        return True  # Default to relevant if check fails

def generate_groq_response(user_query, context, conversation_history):
    """Generate response using Groq API"""
    
    # Build the conversation messages
    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful AI assistant. Use the following context to answer the user's question accurately and comprehensively.

Context: {context}

Instructions:
- Answer the user's question based on the provided context
- If the context contains relevant information, provide a detailed and helpful response
- Be informative and conversational in your tone
- If you notice the context might not be perfectly aligned with the question, still try to extract any relevant information that might be helpful
- Provide specific details, numbers, and facts when available in the context"""
        }
    ]
    
    # Add conversation history
    for message in conversation_history:
        if message.type == "human":
            messages.append({"role": "user", "content": message.content})
        elif message.type == "ai":
            # Skip adding context messages to avoid duplication
            if not message.content.startswith("Context:") and message.content != "No relevant content found.":
                messages.append({"role": "assistant", "content": message.content})
    
    # Add current user query
    messages.append({"role": "user", "content": user_query})
    
    try:
        # Make API call to Groq
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",  # You can change this to other available models
            temperature=0.1,
            max_tokens=1000,
            top_p=1,
            stream=False
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"Error generating response: {str(e)}"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/new-chat', methods=['POST'])
def new_chat():
    """Create a new chat session"""
    try:
        new_session = get_or_create_session()
        
        return jsonify({
            'message': 'New chat session created successfully',
            'session_id': new_session.session_id,
            'created_at': new_session.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'error': f'Failed to create new chat: {str(e)}'}), 500

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    user_query = data.get('query')
    session_id = data.get('session_id')

    if not user_query:
        return jsonify({'error': 'No query provided'}), 400

    # Get or create session
    session = get_or_create_session(session_id)

    context = None
    need_new_search = True

    # Check if we have an existing vector store for this session
    if session.vectorstore:
        # First, try to get relevant results from existing vector store
        retrieved_results = session.vectorstore.similarity_search(user_query, k=3)
        
        if retrieved_results:
            # Get the best match
            best_match = retrieved_results[0].page_content
            
            # Check if the query is actually relevant to the existing context
            is_relevant = check_topic_relevance(user_query, best_match)
            
            if is_relevant:
                context = best_match
                need_new_search = False
                print(f"Session {session.session_id}: Using existing vector store - query is relevant to current topic")
            else:
                print(f"Session {session.session_id}: Query not relevant to existing context - performing new search")
                # Clear memory immediately when topic changes
                session.memory.clear()
                print(f"Session {session.session_id}: Cleared conversation memory for new topic")
        else:
            print(f"Session {session.session_id}: No results found in existing vector store - performing new search")
    
    # If we need new search (either no vectorstore or irrelevant query)
    if need_new_search:
        print(f"Session {session.session_id}: Performing web search for: {user_query}")
        
        # Step 1: Retrieve and scrape content from the web
        links, all_headings, all_paragraphs = search_and_scrape(user_query)

        if not links:
            return jsonify({'error': 'No links found'}), 404

        # Step 2: Process documents and create new vector store
        processed_documents = []
        docs = " ".join(all_headings + all_paragraphs)
        
        if not docs.strip():
            return jsonify({'error': 'No content found to process'}), 404
            
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_texts = text_splitter.split_text(docs)

        # Convert split texts to Document objects
        for text in split_texts:
            if text.strip():  # Only add non-empty texts
                doc = Document(page_content=text)
                processed_documents.append(doc)

        if not processed_documents:
            return jsonify({'error': 'No valid documents to process'}), 404

        # Create new vector store for this session (replaces the old one)
        session.vectorstore = create_vector_store(processed_documents)

        # Perform similarity search for the new query
        retrieved_results = session.vectorstore.similarity_search(user_query, k=1)
        if retrieved_results:
            context = retrieved_results[0].page_content
            print(f"Session {session.session_id}: New context found: {context[:100]}...")
        else:
            context = "No relevant content found in the search results."

    # Ensure we have valid context
    if not context or context.strip() == "":
        context = "No relevant content found for this query."

    # Add user query to memory
    session.memory.chat_memory.add_user_message(user_query)

    # Get conversation history before generating response
    history_messages = session.memory.load_memory_variables({})["history"]

    # Generate response using Groq
    response = generate_groq_response(user_query, context, history_messages)

    # Add AI response to memory
    session.memory.chat_memory.add_ai_message(response)

    # Get updated conversation history and serialize it
    updated_history_messages = session.memory.load_memory_variables({})["history"]
    history = [{"role": message.type, "content": message.content} for message in updated_history_messages]

    return jsonify({
        'response': response, 
        'history': history,
        'session_id': session.session_id,
        'new_search_performed': need_new_search,
        'context_preview': context[:200] + "..." if len(context) > 200 else context  # Debug info
    })

@app.route('/clear', methods=['POST'])
def clear_memory():
    """Clear conversation memory and vector store for a specific session"""
    data = request.json
    session_id = data.get('session_id') if data else None
    
    if session_id and session_id in chat_sessions:
        session = chat_sessions[session_id]
        session.memory.clear()
        session.vectorstore = None
        return jsonify({
            'message': f'Memory and vector store cleared for session {session_id}',
            'session_id': session_id
        })
    else:
        return jsonify({'error': 'Session not found'}), 404

@app.route('/sessions', methods=['GET'])
def get_sessions():
    """Get list of all active chat sessions"""
    sessions_info = []
    for session_id, session in chat_sessions.items():
        sessions_info.append({
            'session_id': session_id,
            'created_at': session.created_at.isoformat(),
            'last_used': session.last_used.isoformat(),
            'has_vectorstore': session.vectorstore is not None,
            'message_count': len(session.memory.load_memory_variables({})["history"])
        })
    
    return jsonify({
        'sessions': sessions_info,
        'total_sessions': len(sessions_info)
    })

@app.route('/delete-session', methods=['POST'])
def delete_session():
    """Delete a specific chat session"""
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400
    
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return jsonify({
            'message': f'Session {session_id} deleted successfully',
            'deleted_session_id': session_id
        })
    else:
        return jsonify({'error': 'Session not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)