import sys
import json
import os

# To import the parser from backend/utils/document_parser
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../backend"))
sys.path.append(backend_path)

from utils.document_parser import extract_text

def process_file(file_path, original_filename):
    try:
        # Extract text using document parser pipeline
        text = extract_text(file_path, original_filename)
        
        if not text:
            raise Exception("No text could be extracted or unsupported file type.")
            
        # Generate summary (simple fallback: first 500 chars)
        summary = text[:500] + "..." if len(text) > 500 else text
        
        print(json.dumps({
            "success": True,
            "extracted_text": text.strip(),
            "summary": summary.strip()
        }))
    except Exception as e:
        print(json.dumps({
            "success": False,
            "message": str(e)
        }))
    finally:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"success": False, "message": "Missing file path or original filename"}))
        sys.exit(1)
        
    process_file(sys.argv[1], sys.argv[2])

