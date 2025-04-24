# 🤖 AI Chatbot Starter Kit

A FastAPI-based starter kit for building AI-powered chatbots with OpenAI (or similar) integration, streaming responses, and database persistence. This project provides a robust and scalable foundation for chatbot development, including optional tool calls via the MCP protocol.

---

## 🚀 Overview

### 🔹 Key Features:

✅ **FastAPI-powered REST API** for managing Assistants, Chats, and Messages.  
✅ **PostgreSQL database** integration with SQLModel & Alembic for persistence.  
✅ **Layered architecture** separating repositories (data access) from services (business logic).  
✅ **Seamless OpenAI integration** for chat completions and real-time streaming responses.  
✅ **MCP protocol support** to enable external tool calls within conversations.  

---

## 🛠️ Core Features

### 🎯 Assistant Management
Effortlessly create, retrieve, and list AI chat assistants with specific configurations tailored to your needs.

### 💬 Chat Management
Start new chat sessions, retrieve past conversations, and handle streaming responses from the LLM.

### 🧠 LLM Integration
Leverage OpenAI (or other compatible LLM services) to power your chatbot with high-quality, context-aware responses.

### 🛎️ Tool Integration via MCP
Extend your chatbot's functionality by integrating external tools that can be invoked dynamically during interactions.

### 📦 Database Management
Store and manage chat data, messages, summaries, and assistant configurations using PostgreSQL.

---

## ⚙️ Configuration

This project uses `pydantic_settings` for managing configurations, loaded via environment variables from a `.env` file.

### 🔑 Required Environment Variables:

```ini
OPENAI_API_KEY=sk-xxxxxx
MCP_SERVER_COMMAND=uv
MCP_SERVER_ARGS=["run","mcp.servers.example.py"]  
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_HOST=localhost
POSTGRES_DB=mydb
POSTGRES_PORT=5432
```

These variables are automatically wired at startup using `Container` in `container.py`.

---

## 🚀 Getting Started

1️⃣ **Clone the repository**
```sh
git clone https://github.com/your-repo/ai-chatbot-starter-kit.git
cd ai-chatbot-starter-kit
```

2️⃣ **Create a virtual environment & install dependencies**
```sh
uv sync
```

3️⃣ **Set up environment variables**
Create a `.env` file in the project root and configure it as shown above.


4️⃣ **Run database migrations**
First you need to spin up the database
```sh
docker compose up
```
Then run the migrations

```sh
alembic upgrade head
```

5️⃣ **Start the FastAPI application**
```sh
uvicorn app.main:app --reload
```

6️⃣ **Access the API documentation**
FastAPI provides interactive API documentation available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📌 Contributing

Contributions are welcome! Feel free to fork this repo, create a feature branch, and submit a pull request.

---

## 🏆 Credits

Developed and maintained by **GonzaData**.

---

## 📜 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---
