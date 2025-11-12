# 📚 Stacknote

> AI organizes. You retrieve.

AI-powered personal knowledge base that automatically organizes, summarizes, and indexes everything you read online.

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- 🤖 **Automatic Categorization** - AI analyzes content and creates topic-based categories
- 📝 **Smart Summaries** - Get 3-5 line summaries with relevant tags
- 🔍 **Semantic Search** - Find content by meaning, not just keywords
- 💬 **AI Chat Interface** - Ask questions about your saved content
- 📊 **Activity Dashboard** - Visualize your learning patterns
- 🔒 **Privacy-First** - Local content extraction with minimal external API calls

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/stacknote.git
cd stacknote

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your UPSTAGE_API_KEY
```

### Configuration

Create a `.env` file in the root directory:
```env
UPSTAGE_API_KEY=your-api-key-here
DEV_MODE=true
```

Get your Upstage API key from [Upstage Console](https://console.upstage.ai).

### Run
```bash
# Using uv
uv run streamlit run app.py

# Or using Python directly
python -m streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## 🛠️ Tech Stack

### Core
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - AI workflow orchestration
- **[Upstage Solar](https://www.upstage.ai/)** - LLM for categorization and summarization
- **[ChromaDB](https://www.trychroma.com/)** - Vector database for semantic search
- **[Trafilatura](https://trafilatura.readthedocs.io/)** - Content extraction

### Framework
- **[Streamlit](https://streamlit.io/)** - Web UI
- **SQLite** - Metadata storage
- **APScheduler** - Background jobs

---

## 📖 Usage

### 1. Save Content
```
1. Paste a URL in the input field
2. Click "Process"
3. AI automatically extracts, categorizes, and summarizes
```

### 2. Search
```
- Use natural language: "LangGraph multi-agent examples"
- Filter by category, date, or tags
- Sort by relevance or date
```

### 3. Chat with AI
```
"What did I learn about RAG this week?"
"Show me all FastAPI tutorials"
"Summarize today's activities"
```

---

## 📂 Project Structure
```
stacknote/
├── app.py              # Streamlit main application
├── core/               # Core functionality
│   ├── extractor.py    # Content extraction
│   ├── agent.py        # AI agent workflow
│   └── storage.py      # Database management
├── config/             # Configuration
│   └── settings.py     # Settings and constants
├── utils/              # Utilities
│   └── logging.py      # Logging setup
├── pages/              # Streamlit pages
├── data/               # Data directory (gitignored)
│   ├── chroma/         # ChromaDB storage
│   └── stacknote.db    # SQLite database
└── logs/               # Logs (gitignored)
```

---

## 🗺️ Roadmap

### Phase 1: MVP (2 weeks) ✅ In Progress
- [x] Project setup
- [ ] Content extraction (Trafilatura)
- [ ] AI categorization and summarization
- [ ] Vector search (ChromaDB)
- [ ] Streamlit UI (Home, Search, Chat)
- [ ] Daily briefing system

### Phase 2: Desktop App (Future)
- [ ] Electron wrapper
- [ ] Native desktop experience
- [ ] Offline support
- [ ] Advanced analytics

### Phase 3: Advanced Features (Future)
- [ ] Browser extension
- [ ] Mobile app
- [ ] Team collaboration
- [ ] API for integrations

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
# Install development dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black .

# Lint
uv run ruff check .
```

---

## 📊 Performance

- URL Processing: < 10 seconds
- Search: < 1 second
- Memory Usage: < 1GB

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the amazing AI framework
- [Upstage](https://www.upstage.ai/) for the Solar LLM API
- [Streamlit](https://streamlit.io/) for the rapid UI development

---

## 📧 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## ⭐ Star History

If you find this project useful, please consider giving it a star!

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/stacknote&type=Date)](https://star-history.com/#yourusername/stacknote&Date)

---

**Built with ❤️ by [Your Name](https://github.com/yourusername)**