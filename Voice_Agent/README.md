# Voice Agent Pharmacy Assistant

This project is a voice-powered pharmacy assistant that allows users to interact with a pharmacy system over the phone. The agent can provide drug information, place orders, and look up existing orders. It uses Twilio for handling phone calls, Deepgram for real-time speech-to-text and text-to-speech, and a WebSocket server to manage the communication flow.

## How It Works

The application follows this architecture:

1.  **Phone Call (User)**: A user calls a Twilio phone number.
2.  **Twilio**: Twilio receives the call and establishes a WebSocket connection with the application server. To make the local server accessible to Twilio, `ngrok` is used to create a public URL.
3.  **WebSocket Server (`main.py`)**: The Python-based WebSocket server, built with the `websockets` library, handles the real-time, bidirectional communication between Twilio and Deepgram.
4.  **Deepgram**:
    *   **Speech-to-Text (STT)**: The server streams the user's audio from Twilio to Deepgram, which transcribes it into text in real-time.
    *   **AI Agent**: The transcribed text is processed by a conversational AI model (configured in `config.json`), which determines the user's intent and what actions to take.
    *   **Function Calling**: If the user's request requires a specific action (e.g., looking up a drug), the AI triggers a function call, which is executed by the server.
    *   **Text-to-Speech (TTS)**: The AI's response is converted back into audio by Deepgram's TTS service.
5.  **Response to User**: The generated audio is streamed back through the WebSocket server to Twilio, which plays it to the user over the phone call.

## Features

*   **Get Drug Information**: Users can ask for information about specific drugs, such as their description, price, and standard quantity.
*   **Place an Order**: Users can place an order for a drug. The system will ask for the user's full name and confirm the order details before processing.
*   **Look Up an Order**: Users can check the status of an existing order by providing their order ID.
*   **User Interruption (Barge-in)**: The system can handle cases where the user speaks before the agent has finished talking.

## Getting Started

### Prerequisites

*   Python 3.10+
*   A Twilio account with a configured phone number
*   A Deepgram API key
*   An OpenAI API key (or another AI provider, as configured in `config.json`)
*   `ngrok` for exposing the local server

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment and install dependencies:**
    The project uses `uv` for package management.
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install uv
    uv pip install -r requirements.txt 
    ```
    *(Note: If a `requirements.txt` is not available, you can create one from `pyproject.toml` or install dependencies manually: `websockets`, `python-dotenv`)*

### Configuration

1.  **Environment Variables**:
    Create a `.env` file in the root of the project and add your API keys:
    ```
    DEEPGRAM_API_KEY=your_deepgram_api_key
    OPENAI_API_KEY=your_openai_api_key
    ```

2.  **`config.json`**:
    This file contains the configuration for the AI agent, including the prompt, the functions it can call, and the models to use for speech-to-text and text-to-speech. You can customize the agent's behavior by modifying this file.

## Running the Application

1.  **Start the WebSocket server:**
    ```bash
    python main.py
    ```
    The server will start on `localhost:5000`.

2.  **Expose the server with ngrok:**
    In a new terminal, run the following command to create a public URL for your local server:
    ```bash
    ngrok http 5000
    ```
    `ngrok` will provide a "Forwarding" URL (e.g., `https://<random-string>.ngrok-free.app`).

3.  **Configure the Twilio Webhook:**
    *   Go to your Twilio account and navigate to the settings for your phone number.
    *   Under "Voice & Fax", find the "A CALL COMES IN" section and set the webhook to the `ngrok` forwarding URL. Make sure to use the WebSocket protocol (`wss://`). For example:
        `wss://<random-string>.ngrok-free.app`
    *   **IMPORTANT**: Every time you restart `ngrok`, you will get a new URL. You must update the Twilio webhook with the new URL each time.

## Functionality Details

The core business logic is defined in `pharmacy_functions.py`:

*   `get_drug_info(drug_name)`: Looks up a drug in the in-memory `DRUG_DB` and returns its details.
*   `place_order(customer_name, drug_name)`: Creates a new order with a predefined quantity and saves it to the in-memory `ORDERS_DB`.
*   `lookup_order(order_id)`: Retrieves an order from the `ORDERS_DB` by its ID.

These functions are mapped to the AI's capabilities through the `FUNCTION_MAP` dictionary and are defined in the `config.json` file to be available for the AI to call.

## Key Dependencies

*   **`websockets`**: For creating the WebSocket server.
*   **`python-dotenv`**: For managing environment variables.
*   **`asyncio`**: For handling asynchronous operations.
