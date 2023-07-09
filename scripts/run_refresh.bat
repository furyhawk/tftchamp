cd backend/pipeline/

python scrape_db.py -c configs/challengers.json --no-load_new
@REM python scrape_db.py -c configs/challenger_oce.json --no-load_new
@REM python scrape_db.py -c configs/grandmasters.json --no-load_new
@REM python scrape_db.py -c configs/masters.json --no-load_new