# Changelog 📋

All notable changes to ScholarEval are documented here.

## [1.0.0] - 2024-01-15

### ✨ Added

#### Security & Validation
- File type validation (PDF only)
- File size limits (max 50MB)
- Filename sanitization (prevent path traversal)
- Input validation for all endpoints
- Request body schema validation
- Comprehensive error messages

#### Backend Improvements
- Complete error handling in all endpoints
- Async-safe file operations (aiofiles)
- Graceful PDF error handling
- JSON validation in LLM responses
- Structured logging throughout
- CORS middleware support
- Health check endpoint
- Status endpoint
- Detailed response structures

#### Frontend Enhancements
- Modern, responsive UI with gradient design
- Real-time file upload feedback
- Proper error display with styling
- Loading states for async operations
- Beautiful evaluation results display
- Points hit/missed breakdown
- Score badge with percentage
- Mobile-responsive design
- Keyboard shortcuts (Ctrl+Enter)
- Auto-scrolling to results
- Health indicator
- Form validation before submission

#### Configuration
- `.env.example` template
- Comprehensive config validation
- Environment variable documentation
- Sensible defaults for all settings

#### Documentation
- `README.md` - Full system documentation
- `QUICKSTART.md` - 5-minute setup guide
- `DEPLOYMENT.md` - Production deployment guide
- `ARCHITECTURE.md` - System design overview
- Inline code documentation

#### Operations
- Setup scripts for Windows (`setup.bat`)
- Setup scripts for macOS/Linux (`setup.sh`)
- Dockerfile for containerization
- docker-compose.yml for easy deployment
- `.gitignore` for version control
- `.dockerignore` for build optimization

#### Dependencies
- Added `aiofiles` for async file I/O
- Updated `requirements.txt` with versions
- Pinned critical dependencies

### 🐛 Fixed

#### Backend
- Fixed blocking file I/O in async endpoints
- Fixed missing error handling in upload
- Fixed JSON parsing issues in LLM response
- Fixed validation bypass in evaluate endpoint
- Fixed typo: "OCR needed" → proper error message

#### Frontend
- Fixed form submission issues
- Fixed alert() UX (replaced with proper UI)
- Fixed missing HTML structure
- Fixed result display (proper variable names)
- Fixed responsive layout

#### Project Structure
- Added missing `__init__.py` files for packages
- Fixed import paths
- Fixed relative imports

### 🚀 Improved

#### Performance
- Optimized PDF text extraction error handling
- Improved RAG index building
- Better chunk merging in hybrid search

#### Code Quality
- Type hints in function signatures
- Comprehensive docstrings
- Structured error responses
- Proper logging levels
- Code organization

#### User Experience
- Beautiful UI with modern design
- Clear error messages
- Helpful file upload guidance
- Smart validation feedback
- Real-time status updates

#### Deployment
- Docker support for containerization
- Production-ready configuration
- Systemd service template included
- Nginx reverse proxy examples
- SSL/TLS setup guides

### 📦 Dependencies Updated

```
fastapi>=0.104.0      (was: no version pin)
uvicorn>=0.24.0       (was: no version pin)
pymupdf>=1.23.0       (was: no version pin)
faiss-cpu>=1.7.0      (was: no version pin)
sentence-transformers>=2.2.0  (was: no version pin)
rank-bm25>=0.2.2      (was: no version pin)
numpy>=1.24.0         (was: no version pin)
python-dotenv>=1.0.0  (was: no version pin)
mistralai>=0.4.0      (was: no version pin)
aiofiles>=23.2.0      (NEW)
```

## Files Changed

### Modified
- `main.py` - Complete refactor with error handling, validation, async operations
- `backend/core/config.py` - Enhanced configuration management
- `backend/core/pdf_manager.py` - Added error handling and logging
- `backend/core/llm_service.py` - JSON parsing, validation, error handling
- `frontend/index.html` - Complete UI redesign with modern styling
- `requirements.txt` - Pinned versions

### Added
- `backend/__init__.py` - Package marker
- `backend/core/__init__.py` - Package marker
- `.env.example` - Configuration template
- `.gitignore` - Version control rules
- `.dockerignore` - Docker build optimization
- `setup.bat` - Windows setup script
- `setup.sh` - Unix setup script
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Container orchestration
- `README.md` - Full documentation
- `QUICKSTART.md` - Quick start guide
- `DEPLOYMENT.md` - Deployment guide
- `ARCHITECTURE.md` - System architecture
- `CHANGELOG.md` - This file

## Breaking Changes

None - This is the initial production-ready version.

## Migration Guide

If upgrading from pre-1.0.0:
1. Copy new `backend/__init__.py` files
2. Update `main.py` with error handling
3. Update requirements.txt versions
4. Create `.env` from `.env.example`
5. Test PDF upload workflow

## Known Limitations

- RAG index not persisted (resets on server restart)
- Single-server deployment (no clustering)
- In-memory embeddings only
- No authentication/authorization
- CORS allows all origins (restrict for production)
- No rate limiting implemented yet

## Future Roadmap

- [ ] Persist RAG indices to disk
- [ ] Redis caching for embeddings
- [ ] Authentication (API keys, OAuth2)
- [ ] Rate limiting per user/IP
- [ ] Batch evaluation API
- [ ] Multi-language support
- [ ] Custom embedding models
- [ ] Audit logging
- [ ] Web dashboard
- [ ] Monitoring/observability
- [ ] Database backend (PostgreSQL)
- [ ] Dedicated worker queue (Celery)

## Contributors

Initial development and production hardening completed.

## License

MIT License - See LICENSE file

## Support

For issues, questions, or suggestions:
1. Check [TROUBLESHOOTING](#troubleshooting) in README.md
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design details
3. Check inline code comments
4. Open an issue with details

---

**ScholarEval v1.0.0** - Production-ready AI Answer Evaluation System 🚀
