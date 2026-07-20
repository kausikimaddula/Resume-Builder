"""Integration test for the /resume/upload route and parser service."""

from app import app
from pathlib import Path

def test_upload_flow():
    # Make sure files exist
    docx_path = Path("test_resume.docx")
    pdf_path = Path("test_resume.pdf")
    
    if not docx_path.exists() or not pdf_path.exists():
        print("Please run generate_test_resumes.py first to generate test files.")
        return False
        
    app.config["WTF_CSRF_ENABLED"] = False
    
    with app.test_client() as client:
        # 1. Test DOCX upload
        print("Testing DOCX upload...")
        with open(docx_path, "rb") as docx_file:
            response = client.post(
                "/resume/upload",
                data={"resume_file": (docx_file, "test_resume.docx")},
                follow_redirects=True
            )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        html = response.get_data(as_text=True)
        assert "Jane Doe - Resume" in html, "Could not find 'Jane Doe - Resume' in response html"
        assert "Languages" in html, "Could not find 'Languages' in response html"
        assert "Python, HTML, CSS, JavaScript" in html, "Could not find skills in response html"
        print("DOCX upload integration test passed!")
        
        # 2. Test PDF upload
        print("Testing PDF upload...")
        with open(pdf_path, "rb") as pdf_file:
            response = client.post(
                "/resume/upload",
                data={"resume_file": (pdf_file, "test_resume.pdf")},
                follow_redirects=True
            )
            
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        html = response.get_data(as_text=True)
        assert "John Smith - Resume" in html, "Could not find 'John Smith - Resume' in response html"
        assert "Cloud Engineer" in html, "Could not find 'Cloud Engineer' in response html"
        print("PDF upload integration test passed!")
        
        # 3. Test Invalid Extension upload
        print("Testing invalid file extension (should be rejected)...")
        # Try uploading this script itself which has .py extension
        with open(__file__, "rb") as invalid_file:
            response = client.post(
                "/resume/upload",
                data={"resume_file": (invalid_file, "test_integration.py")},
                follow_redirects=True
            )
        html = response.get_data(as_text=True)
        # Should render validation error
        assert "Only DOCX and PDF files are allowed" in html, "Expected file type validation error page/alert"
        print("Invalid file type validation test passed!")

    print("All integration tests passed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_upload_flow()
        if not success:
            import sys
            sys.exit(1)
    except AssertionError as e:
        print(f"Assertion failed: {e}")
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import sys
        sys.exit(1)
