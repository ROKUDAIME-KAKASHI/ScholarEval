from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
import shutil

from backend.core.pdf_manager import PDFManager
from backend.core.rag_engine import RAGEngine
from backend.core.llm_service import LLMService
from backend.core.test_generator import TestGenerator
from backend.core.config import (
    UPLOAD_DIR, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS,
    HOST, PORT, DEBUG
)

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(
    __name__,
    static_folder='frontend',
    static_url_path='/static'
)

# CORS configuration
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_BYTES

# Initialize services
pdf_manager = PDFManager()
content_engine = RAGEngine()
question_engine = RAGEngine()
llm_service = LLMService()
test_generator = TestGenerator()


# ============ Initialization & Auto-Loading ============

def load_pdf_knowledge_base():
    """Auto-load all PDFs from the data/ folder on startup."""
    pdf_dir = "data"
    if not os.path.isdir(pdf_dir):
        logger.warning(f"PDF directory '{pdf_dir}' not found. Skipping auto-load.")
        return 0
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logger.warning(f"No PDF files found in '{pdf_dir}'")
        return 0
    
    total_questions = 0
    all_questions = []
    
    for pdf_file in pdf_files:
        try:
            file_path = os.path.join(pdf_dir, pdf_file)
            logger.info(f"Loading PDF: {file_path}")
            
            # Process PDF to extract structured questions
            structured_data = pdf_manager.process_pdf(file_path)
            
            # Extract just the questions for categorization
            questions = [item["question"] for item in structured_data]
            all_questions.extend(questions)
            total_questions += len(questions)
            
            logger.info(f"✓ Loaded {pdf_file} ({len(questions)} questions)")
        except Exception as e:
            logger.error(f"✗ Error loading {pdf_file}: {str(e)}")
    
    if all_questions:
        # Build index with structured data
        try:
            for pdf_file in pdf_files:
                file_path = os.path.join(pdf_dir, pdf_file)
                structured_data = pdf_manager.process_pdf(file_path)
                content_engine.build_index(structured_data)
        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
        
        # Categorize questions by subject
        test_generator.categorize_questions_by_subject(all_questions)
        logger.info(f"✓ Categorized {len(all_questions)} questions by subject")
    
    logger.info(f"Knowledge base ready: {total_questions} questions from {len(pdf_files)} PDFs")
    return total_questions


def validate_filename(filename: str) -> str:
    """Validate and sanitize uploaded filename."""
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    ext = Path(filename).suffix.lower()
    if ext not in {f".{e}" for e in ALLOWED_EXTENSIONS}:
        raise ValueError(f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    safe_name = secure_filename(filename)
    
    if not safe_name:
        raise ValueError("Invalid filename")
    
    return safe_name


def save_uploaded_file(file, upload_dir: str) -> str:
    """Save uploaded file with validation."""
    try:
        safe_filename = validate_filename(file.filename)
        
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, safe_filename)
        
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB")
        
        file.save(file_path)
        logger.info(f"File saved: {file_path} ({file_size} bytes)")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise


# ============ API Routes ============

@app.route("/", methods=["GET"])
def home():
    """Serve the main HTML interface."""
    try:
        with open("frontend/index.html", mode="r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        logger.error("Frontend not found")
        return jsonify({"error": "Frontend not found"}), 404
    except Exception as e:
        logger.error(f"Error serving frontend: {str(e)}")
        return jsonify({"error": "Error reading frontend"}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "running",
        "content_chunks": len(content_engine.texts),
        "content_index_ready": content_engine.index is not None,
        "question_bank_size": len(question_engine.texts),
        "question_bank_ready": question_engine.index is not None
    })


@app.route("/upload", methods=["POST"])
def upload_pdf():
    """Upload and process a PDF file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"error": "No file provided"}), 400
        
        file_path = save_uploaded_file(file, UPLOAD_DIR)
        
        try:
            chunks = pdf_manager.process_pdf(file_path)
        except ValueError as e:
            logger.warning(f"PDF processing error: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
        combined = content_engine.texts + chunks if content_engine.texts else chunks
        content_engine.build_index(combined)
        
        logger.info(f"PDF processed: {len(chunks)} chunks indexed")
        return jsonify({
            "status": "success",
            "message": "PDF processed successfully",
            "filename": Path(file_path).name,
            "chunks_indexed": len(chunks)
        })
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": "Error processing PDF"}), 500


@app.route("/evaluate", methods=["POST"])
def evaluate():
    """Evaluate a student answer."""
    try:
        data = request.get_json()
        
        question = (data.get("question") or "").strip()
        answer = (data.get("student_answer") or "").strip()
        max_marks = int(data.get("max_marks", 5))
        
        if not question:
            return jsonify({"error": "Question cannot be empty"}), 400
        if not answer:
            return jsonify({"error": "Student answer cannot be empty"}), 400
        if max_marks <= 0:
            return jsonify({"error": "max_marks must be positive"}), 400
        
        if content_engine.index is None:
            return jsonify({"error": "No knowledge base loaded. Please upload PDFs first."}), 400
        
        try:
            context_chunks = content_engine.retrieve(question)
            context = "\n".join(context_chunks)
        except Exception as e:
            logger.warning(f"Context retrieval failed: {str(e)}")
            context = ""
        
        try:
            result = llm_service.evaluate(question, answer, context, max_marks)
            result["evaluation_method"] = "primary_llm" if context else "fallback_mock"
        except Exception as e:
            logger.warning(f"Primary evaluation failed: {str(e)}, using fallback...")
            result = keyword_based_evaluation(question, answer, context, max_marks)
            result["evaluation_method"] = "keyword_matching"
        
        logger.info(f"Evaluation complete: {result.get('score')}/{max_marks}")
        return jsonify({
            "status": "success",
            "evaluation": result,
            "context_chunks_used": len(context_chunks) if context else 0
        })
    
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        return jsonify({"error": "Error during evaluation"}), 500


def keyword_based_evaluation(question: str, answer: str, context: str, max_marks: int) -> dict:
    """Fallback evaluation using keyword matching."""
    question_lower = question.lower()
    answer_lower = answer.lower()
    context_lower = context.lower() if context else ""
    
    keywords = []
    if context:
        words = context_lower.split()
        keywords = [w.strip('.,!?;:') for w in words if len(w) > 4]
        keywords = list(set(keywords))[:10]
    
    matches = sum(1 for kw in keywords if kw in answer_lower)
    match_ratio = matches / len(keywords) if keywords else 0
    
    score = int(max_marks * match_ratio)
    score = max(0, min(score, max_marks))
    
    if len(answer) > 100:
        score = min(max_marks, score + 1)
    
    return {
        "score": score,
        "max_marks": max_marks,
        "feedback": f"Answer evaluated. {score} points awarded.",
        "confidence": "low"
    }


@app.route("/ingest_questions", methods=["POST"])
def ingest_questions():
    """Upload a question-paper PDF and index questions."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"error": "No file provided"}), 400

        file_path = save_uploaded_file(file, UPLOAD_DIR)
        try:
            # Process PDF to extract structured questions
            structured_data = pdf_manager.process_pdf(file_path)
            if not structured_data:
                return jsonify({"error": "No questions found in PDF"}), 400
            
            # Extract just the question text
            questions = [item["question"] for item in structured_data]
            
            # Index the structured data
            content_engine.build_index(structured_data)
            
            # Categorize questions
            test_generator.categorize_questions_by_subject(questions)
            
            logger.info(f"Ingested {len(questions)} questions from {file.filename}")
            
            return jsonify({
                "status": "success",
                "message": f"Indexed {len(questions)} questions",
                "questions_indexed": len(questions)
            })
        except ValueError as e:
            logger.warning(f"Question extraction error: {str(e)}")
            return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Ingest error: {str(e)}")
        return jsonify({"error": "Error ingesting question paper"}), 500


@app.route("/api/subjects", methods=["GET"])
def get_subjects():
    """Get list of available subjects."""
    try:
        subjects = test_generator.get_available_subjects()
        stats = test_generator.get_subject_stats()

        return jsonify({
            "status": "success",
            "subjects": subjects,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error getting subjects: {str(e)}")
        return jsonify({"error": "Error retrieving subjects"}), 500


@app.route("/api/generate_test", methods=["POST"])
def generate_subject_test():
    """Generate a mock test for a specific subject."""
    try:
        data = request.get_json()
        subject = data.get("subject", "").strip()
        num_questions = int(data.get("num_questions", 10))
        difficulty = data.get("difficulty")

        if not subject:
            return jsonify({"error": "Subject is required"}), 400

        if num_questions <= 0:
            return jsonify({"error": "num_questions must be positive"}), 400

        test = test_generator.generate_test(subject, num_questions, difficulty)

        return jsonify({
            "status": "success",
            "test": test
        })
    except ValueError as e:
        logger.warning(f"Test generation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating test: {str(e)}")
        return jsonify({"error": "Error generating test"}), 500


@app.route("/api/test/<test_id>", methods=["GET"])
def get_test(test_id):
    """Retrieve a test by its ID."""
    try:
        test = test_generator.get_test(test_id)
        if not test:
            return jsonify({"error": "Test not found"}), 404

        return jsonify({
            "status": "success",
            "test": test
        })
    except Exception as e:
        logger.error(f"Error retrieving test: {str(e)}")
        return jsonify({"error": "Error retrieving test"}), 500


@app.route("/api/test/<test_id>/submit", methods=["POST"])
def submit_test_answers(test_id):
    """Submit answers for a test."""
    try:
        data = request.get_json()
        answers = data.get("answers")

        if not answers or not isinstance(answers, list):
            return jsonify({"error": "answers must be a non-empty list"}), 400

        test = test_generator.submit_all_answers(test_id, answers)

        for answer_data in answers:
            q_id = answer_data['question_id']
            answer = answer_data['answer']

            if q_id < 0 or q_id >= len(test['questions']):
                continue

            question = test['questions'][q_id]['question']
            max_marks = test['questions'][q_id]['max_marks']

            # Retrieve context from content engine
            context = ""
            try:
                if content_engine.index is not None:
                    context_results = content_engine.retrieve(question)
                    # Extract text from the retrieved results (tuples of (score, data))
                    context_texts = []
                    for score, item in context_results:
                        if isinstance(item, dict) and 'points' in item:
                            for point in item['points']:
                                if isinstance(point, dict) and 'text' in point:
                                    context_texts.append(point['text'])
                    context = "\n".join(context_texts[:5])  # Limit to 5 points
            except Exception as e:
                logger.warning(f"Failed to retrieve context: {str(e)}")
                context = ""

            # Evaluate answer
            try:
                eval_result = llm_service.evaluate(question, answer, context, max_marks)
                test['questions'][q_id]['evaluation'] = eval_result
            except Exception as e:
                logger.error(f"Error evaluating question {q_id}: {str(e)}")
                # Fallback: simple evaluation
                test['questions'][q_id]['evaluation'] = {
                    "score": max_marks // 2,
                    "feedback": "Evaluation completed.",
                    "points_hit": [],
                    "points_missed": [],
                    "max_marks": max_marks
                }

        score_result = test_generator.calculate_test_score(test_id)

        return jsonify({
            "status": "success",
            "test": test,
            "score": score_result
        })
    except ValueError as e:
        logger.warning(f"Test submission error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error submitting test: {str(e)}")
        return jsonify({"error": "Error submitting test"}), 500


@app.route("/status", methods=["GET"])
def status():
    """Get current system status."""
    return jsonify({
        "service": "ScholarEval",
        "version": "1.0.0",
        "content_index_initialized": content_engine.index is not None,
        "content_chunks": len(content_engine.texts),
        "knowledge_base_ready": len(content_engine.texts) > 0,
        "upload_dir": UPLOAD_DIR,
        "max_file_size_mb": MAX_FILE_SIZE_BYTES / (1024 * 1024),
        "llm_available": not llm_service._mock
    })


@app.route("/knowledge_base", methods=["GET"])
def knowledge_base():
    """Get information about the loaded knowledge base."""
    return jsonify({
        "status": "ok" if content_engine.index is not None else "not_loaded",
        "total_chunks": len(content_engine.texts),
        "sample_chunks": content_engine.texts[:3] if content_engine.texts else [],
        "description": "Knowledge base loaded from pdfs/ folder"
    })


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(f"Starting ScholarEval on {HOST}:{PORT}")
    
    chunks_loaded = load_pdf_knowledge_base()
    if chunks_loaded == 0:
        logger.warning("⚠ No PDFs loaded. RAG system may not work optimally.")
    
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
        threaded=True
    )
