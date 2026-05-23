import sys, importlib.util, os
sys.path.insert(0, os.path.dirname(__file__))

spec = importlib.util.spec_from_file_location("upload", os.path.join(os.path.dirname(__file__), "steps", "07_upload.py"))
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)

creds = upload._get_credentials()
print("Auth complete! Token saved to youtube_token.json")
