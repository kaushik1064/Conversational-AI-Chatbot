Here's a detailed documentation on how the code works, along with instructions on how to run it.


## **Project Overview**

This project is a conversational AI chatbot built using Flask, Langchain, and OpenAI's GPT model. The chatbot can hold a conversation with users, remember previous interactions, and respond in context based on the conversation history. The front-end is built using HTML, CSS, and Bootstrap, providing a simple and clean interface for users to interact with the chatbot.

## **Project Structure**

```
/project-directory
|-- app.py
|-- /templates
|   |-- index.html
|-- /utils
|   |-- search_and_scrape.py
|   |-- vector_store.py
|   |-- web_loader.py
```

### **Files and Their Purpose:**

1. **`app.py`**: 
   - The main application file. It initializes the Flask app, sets up the Langchain memory, and handles user queries.
   - Renders the front-end interface and processes AJAX requests to provide chatbot responses.

2. **`index.html`**:
   - The front-end HTML file located in the `templates` directory. It provides the user interface for interacting with the chatbot.

3. **`search_and_scrape.py`**:
   - Utility file responsible for web scraping and searching. (Specifics not detailed in this documentation as it’s utility-specific).

4. **`vector_store.py`**:
   - Utility file responsible for handling vector storage for memory. (Specifics not detailed in this documentation as it’s utility-specific).

5. **`web_loader.py`**:
   - Uses the `WebBaseLoader` from `langchain_community.document_loaders` to load content from a webpage. It filters content using `bs4.SoupStrainer` to focus on specific classes.
   - Utilizes `RecursiveCharacterTextSplitter` from Langchain to split the loaded web content into manageable chunks for further processing.


## **How It Works**

### **1. Flask Application (`app.py`)**

- **Imports and Setup**:
  - Imports necessary libraries including Flask, Langchain, OpenAI, and environment variables.
  - Sets up environment variables using `dotenv` to load the OpenAI API key.

- **Memory and Langchain Setup**:
  - `ConversationBufferMemory`: Used to maintain a memory of previous user and system messages, enabling contextual conversation.
  - `LLMChain`: Wraps the GPT model with a prompt template to generate responses based on user queries.

- **Routes**:
  - **`/` (GET)**: Renders the `index.html` template, displaying the chatbot interface.
  - **`/query` (POST)**: Handles the user's query. The query is processed using the `LLMChain`, and the response is sent back to the front-end. Additionally, the conversation history is returned and displayed.

### **2. Front-End Interface (`index.html`)**

- **User Interface**:
  - A simple, responsive design using Bootstrap.
  - A chat container displays the conversation history with the AI, while an input field allows users to type their queries.

- **AJAX Handling**:
  - JavaScript handles form submission, sending the user’s query to the Flask backend without reloading the page.
  - The chatbot’s response is then appended to the chat container, maintaining the conversation flow.

### **3. Web Scraping and Vector Store (Utilities)**

- **Web Scraping (`search_and_scrape.py`)**:
  - Handles scraping and retrieving information from websites, useful for retrieving data needed for the chatbot.

- **Vector Store (`vector_store.py`)**:
  - Manages the vector storage for memory, ensuring that the chatbot can remember and recall previous conversations.

## **Instructions to Run the Code**

### **1. Prerequisites**

Ensure you have the following installed:

- **Python 3.7+**
- **pip** (Python package installer)

### **2. Install Required Packages**

Create and activate a virtual environment (optional but recommended):

```bash
conda create -p venv python==3.11 -y
conda activate venv/ 
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### **3. Set Up Environment Variables**

Create a `.env` file in the root directory of your project and add your HuggingFaceHub API key:

```bash
HUGGINGFACEHUB_API_TOKEN="your_HUGGINGFACEHUB_API_TOKEN"
```

```bash
GROQ_API_KEY="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"
```

### **4. Run the Flask Application**

Run the Flask application using:

```bash
python app.py
```

By default, the Flask app will run on `http://127.0.0.1:5000/`. Open this URL in your browser to interact with the chatbot.

### **5. Using the Chatbot**

- Enter your query in the input field and click "Send".
- The chatbot will respond, and you can continue the conversation.
- The chatbot remembers previous interactions, so you can ask follow-up questions, and it will respond based on the context of the conversation.

### **6. Customization**

- **Front-End**: You can customize the `index.html` file to change the appearance or add more features to the UI.
- **Backend**: Modify `app.py` to add more functionality or tweak the conversation logic.


### **Flowchart**

The flowchart below illustrates the process flow of the conversational AI app:


### **Flowchart Image**

![Flowchart](D:/deepedge/systematic_flowchart.jpg)
