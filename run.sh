cd app;../../bin/python3 minute_fetcher.py;../../bin/python3 minute_analyzer.py;../../bin/python3 -m uvicorn feederAPI:app --host 127.0.0.1 --port 8000 & # API起動
cd ../frontend;../../bin/python3 -m http.server 8001 --bind 127.0.0.1
