../bin/python3 app/fetch.py --municipality Tokyo;

cd app;
../../bin/python3 minute_analyzer.py;
../../bin/python3 -m uvicorn feederAPI:app --host localhost --port 8000 & # API起動

cd ../frontend;
../../bin/python3 -m http.server 8001 --bind localhost
