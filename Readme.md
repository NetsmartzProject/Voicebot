# Conversational AI with Speech Transcription 🎙️🤖

A real-time voice assistant powered by Deepgram (Speech-to-Text & Text-to-Speech) and ChatGroq (Large Language Model) using LangChain for conversation memory. The system transcribes speech, generates AI responses, and converts text back into speech for a seamless interactive experience.

---

## 🚀 Features

✅ **Real-time Speech Recognition** – Uses Deepgram for fast and accurate speech-to-text (STT).  
✅ **Conversational AI** – Integrates Groq's ChatGroq (Gemma2-9B-IT) for intelligent responses.  
✅ **Context-Aware Memory** – Utilizes LangChain's ConversationBufferMemory.  
✅ **Text-to-Speech (TTS)** – Deepgram converts responses into natural-sounding speech.  
✅ **End-to-End Automation** – Listens, processes, and speaks back in a continuous loop.  
✅ **Streamlit UI** – Interactive interface for easy interaction and monitoring.  

---

## 🛠 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/conversational-ai-voicebot.git
cd conversational-ai-voicebot
```

### 2️⃣ Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv env
source env/bin/activate  # On macOS/Linux
env\Scripts\activate    # On Windows
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Environment Variables
Create a `.env` file in the root directory and add the following credentials:
```env
DEEPGRAM_API_KEY=your_deepgram_api_key
GROQ_API_KEY=your_groq_api_key
```

---

## 🎯 Usage

### 1️⃣ Run the Application
```bash
streamlit run main.py
```

### 2️⃣ Interact with the Voice Assistant
- Click the **Start Listening** button.
- Speak into your microphone.
- The AI transcribes, processes, and responds using speech.

---
---

## 📌 Dependencies
- **Deepgram** – Speech-to-Text & Text-to-Speech
- **Groq (ChatGroq)** – Large Language Model
- **LangChain** – Conversation memory management
- **Streamlit** – Interactive UI

---

## 🚀 Future Enhancements
- 🔹 Support for multiple languages
- 🔹 Customizable voice selection
- 🔹 Integration with WhatsApp & Telegram bots
