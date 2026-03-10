# Enterprise RAG Chatbot

An intelligent enterprise chatbot capable of answering questions based on internal documentation using Retrieval-Augmented Generation (RAG).

This project was developed as part of a **Computer Engineering capstone project**, exploring how Large Language Models can be applied to enterprise knowledge management.

---

# Problem

Organizations often store critical knowledge in internal documents such as:

- Standard Operating Procedures (SOPs)
- Internal manuals
- Process documentation
- Technical guidelines

However, retrieving specific information from these documents is often slow and inefficient.

Employees frequently spend significant time searching through multiple files to find relevant information.

---

# Solution

This project implements a **Retrieval-Augmented Generation (RAG)** architecture to allow users to ask natural language questions and receive answers grounded in real documentation.

The system works by:

1. Ingesting internal documents
2. Splitting documents into chunks
3. Generating embeddings for each chunk
4. Storing embeddings in a vector database
5. Retrieving relevant context for each user query
6. Using a Large Language Model to generate contextual answers

---

# System Architecture

Main components of the system:

- Document ingestion pipeline
- Embedding generation
- Vector database
- Retrieval engine
- LLM response generation
- Web interface

*(Architecture diagram coming soon)*

---

# Technologies Used

### Backend

- Python
- FastAPI

### AI / Machine Learning

- Retrieval-Augmented Generation (RAG)
- Vector Databases (ChromaDB / FAISS)
- Embedding models
- Large Language Models

### Frontend

- HTML
- CSS
- JavaScript

---

# Features

- Semantic document search
- Context-aware answer generation
- Modular architecture
- Web interface for interaction

---

# Future Improvements

- Authentication and user management
- Multi-document ingestion pipeline
- Docker deployment
- Integration with enterprise knowledge bases

---

# Author

Matheus Novais Rocha  
Automation and Data Engineer
