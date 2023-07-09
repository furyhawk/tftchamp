#!/bin/sh

if command -v caffeinate &> /dev/null
then
    echo "<caffeinate> found"
    caffeinate -i -w $$ &
fi


# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

usage="$(basename "$0") [-h] [-nri] [-mgc] [-a] -- Team Fight Tactic pipeline helper

where:
    -h  show this help text
    -n  Scraping for new summoners (default=0)
    -r  Scraping for new matches (default=1)
    -i  Transforming and infering matches (default=0)
    -m  run above for master league (default=0)
    -g  run above for grandmaster league (default=0)
    -c  run above for challenger league (default=1)
    -a  run all above (default=0)"

# Initialize our own variables:
run_new=0
run_refresh=1
run_infer=0
run_master=0
run_grandmaster=0
run_challenger=1

while getopts "h?anrimgc" opt; do
  case ${opt} in
    h|\?)
      echo "$usage"
      exit 0
      ;;
    a)  run_new=1
        run_refresh=1
        run_infer=1
        run_master=1
        run_grandmaster=1
        run_challenger=1
        ;;
    n)  run_new=1
        ;;
    r)  run_refresh=1
        ;;
    i)  run_infer=1
        ;;
    m)  run_master=1
        ;;
    g)  run_grandmaster=1
        ;;
    c)  run_challenger=1
        ;;
    :)  printf "missing argument for -%s\n" "$OPTARG" >&2
        echo "$usage" >&2
        exit 1
        ;;
    \?) printf "illegal option: -%s\n" "$OPTARG" >&2
        echo "$usage" >&2
        exit 1
        ;;
  esac
done

shift $((OPTIND-1))

[ "${1:-}" = "--" ] && shift

ROOTPWD=${PWD}
cd backend/pipeline/

echo "Running run_new=${run_new} run_refresh=${run_refresh} run_infer=${run_infer} in ${PWD}"
echo "Running run_master=${run_master} run_grandmaster=${run_grandmaster} run_challenger=${run_challenger}"

if [[ $run_new = 1 ]]; then
    echo "Scraping for new summoners."
    if [[ $run_master = 1 ]]; then
        python scrape_db.py -c configs/masters.json --load_new -m 1
    fi
    if [[ $run_grandmaster = 1 ]]; then
        python scrape_db.py -c configs/grandmasters.json --load_new -m 1
    fi
    if [[ $run_challenger = 1 ]]; then
        python scrape_db.py -c configs/challengers.json --load_new -m 1
    fi
fi

if [[ $run_refresh = 1 ]]; then
    echo "Scraping for new matches."
    if [[ $run_master = 1 ]]; then
        python scrape_db.py -c configs/masters.json --no-load_new
    fi
    if [[ $run_grandmaster = 1 ]]; then
        python scrape_db.py -c configs/grandmasters.json --no-load_new
    fi
    if [[ $run_challenger = 1 ]]; then
        python scrape_db.py -c configs/challengers.json --no-load_new
    fi
fi

if [[ $run_infer = 1 ]]; then
    echo "Transforming and infering matches."
    if [[ $run_master = 1 ]]; then
        python data_loading_db.py -c configs/masters.json
        python team_composition_db.py -c configs/masters.json
        python optimizer.py -c configs/config_xgb_m.json
        python optimizer.py -c configs/config_xgb_m_euw.json
        python optimizer.py -c configs/config_xgb_m_kr.json
    fi
    if [[ $run_grandmaster = 1 ]]; then
        python data_loading_db.py -c configs/grandmasters.json
        python team_composition_db.py -c configs/grandmasters.json
        python optimizer.py -c configs/config_xgb_gm.json
    fi
    if [[ $run_challenger = 1 ]]; then
        python data_loading_db.py -c configs/challengers.json
        python team_composition_db.py -c configs/challengers.json
        python optimizer.py -c configs/config_xgb_euw.json
        python optimizer.py -c configs/config_xgb_kr.json
        python optimizer.py -c configs/config_xgb.json
    fi

    latestFeatureImportance=`ls -td saved/XGBRegressor/*/XGBRegressor_feature_importances.png | head -1`
    latestActualVsPredict=`ls -td saved/XGBRegressor/*/XGBRegressor_ActualvsPredicted.png | head -1`
    latestModel=`ls -td saved/XGBRegressor/*/model.pkl | head -1`
    echo "Copying ${latestFeatureImportance} ..."
    cp -fr $latestFeatureImportance ../../assets/XGBRegressor_feature_importances.png
    cp -fr $latestActualVsPredict ../../assets/XGBRegressor_ActualvsPredicted.png
    cp -fr $latestModel ../app/saved/challengers/model.pkl
fi

cd $ROOTPWD
