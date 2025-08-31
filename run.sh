../../bin/python3 fetch.py --municipality setagaya;../../bin/python3 app/minute_analyzer.py;../../bin/python3 -m uvicorn app.feederAPI:app --host localhost --port 8000 & # API起動
cd frontend;../../bin/python3 -m http.server 8001 --bind localhost
