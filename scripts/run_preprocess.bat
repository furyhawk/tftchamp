cd backend/pipeline/

python data_loading_db.py -c configs/challengers.json
@REM python data_loading_db.py -c configs/grandmasters.json
@REM python data_loading_db.py -c configs/masters.json
python team_composition_db.py -c configs/challengers.json
@REM python team_composition_db.py -c configs/grandmasters.json
@REM python team_composition_db.py -c configs/masters.json
@REM python optimizer.py -c configs/config_xgb_m.json
@REM python optimizer.py -c configs/config_xgb_m_euw.json
@REM python optimizer.py -c configs/config_xgb_m_kr.json
@REM python optimizer.py -c configs/config_xgb_gm.json
python optimizer.py -c configs/config_xgb_euw.json
python optimizer.py -c configs/config_xgb_kr.json
python optimizer.py -c configs/config_xgb.json