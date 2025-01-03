from prometheus_client import start_http_server,  Summary, Gauge,  Counter, Info
import time
import os
#from requests.exceptions import ConnectionError
import requests
from requests.adapters import HTTPAdapter
import logging
import urllib3
from urllib3.util.retry import Retry
# from urllib3 import PoolManager

# Create metrics.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
ATTESTATION_EFFECTIVENESS = Gauge("validator_effectiveness" , 'Attestation effectiveness percentage',['validator'])
RANK = Gauge("validator_rank" , 'Rank among validators - 1 day sliding',['validator','range'])
PERFORMANCE = Gauge("validator_performance" , 'Performance',['validator','range'])
REWARD = Gauge("validator_reward" , 'Rewards for actions',['validator','type'])
PENALTY = Gauge("validator_penalty" , 'Penalty for actions',['validator','type'])

INFO = Info('validator_status' ,'Information about on-chain validator')
RATELIMIT = Gauge("rate_limit_remain" , 'Remaining Hits per periode',['type'])

# initial settings
current_epoch = 0
current_finalized_epoch = 0
current_slot = 0

# wait time between API request
sleep_delay = 25

logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

INFO.info ({'status': 'unknown' })


#
# request scheduler
#
def process_request(validator):
    """A dummy function that takes some time."""
    blockchain_state (validator)
    time.sleep(sleep_delay)
    validator_performance (validator)
    time.sleep(sleep_delay)
    validator_efficiency (validator)
    time.sleep(sleep_delay)
    validator_info (validator)
    time.sleep(sleep_delay)
    validator_reward(validator)
    time.sleep(sleep_delay)
    #blockchain_state (validator)

def help():
    print ("ETH validator prometheus exporter from beaconcha.in API\n")
    print ("env CHAIN: mainnet(default) or holesky\n")
    print ("    VALIDATOR: pubkey or number of the validator\n")
    print ("    LOG: loglevel (DEBUG,INFO,WARNING,CRITICAL) default: INFO\n")


# Function to access beacon API and ensure that we do not hammer the endpoint

# Decorate function with metric.
@REQUEST_TIME.time()
def api_fetcher_json (url):
    """
    The main getter for API requests.

    handles timeouts and requests limits 
    """
    # Time Limits and pause values (seconds)
    rate_limit = {
        'Month': 20000,
        'Day': 14400,
        'Hour': 1800,
        'Minute': 40, 
        'Second': 2
    }

    try:
 
        response = requests.get( url )
        response.raise_for_status()
        logger.debug(response.headers)
        logger.info(f"Response: {response.content}")
        # Rate limit Gauge
        for inter in rate_limit.keys ():
            RATELIMIT.labels(inter).set (response.headers['X-Ratelimit-Remaining-' + inter])
            # if (response.headers['X-Ratelimit-Remaining-' + inter])
            # REWARD.labels(validator,'head').set(int(API_Data['data'][0]['income'].get('attestation_head_reward',0)))
        # response = requests.get( url )
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        time.sleep (60)
        return { 'status' : 'KO'}
    except requests.exceptions.HTTPError as e:
        logger.debug(response.headers)
        logger.error(f"HTTP error: {e}")
        # Specific code for rate limiting
        # Retry-After': '1217202
        if response.status_code == 429:
            logger.error("API endpoint Rate limited exceeded\n")
            for inter in rate_limit.keys ():
                if (response.headers['X-Ratelimit-Remaining-' + inter]) == '0':
                    logger.error(f"Limit reached ({inter}):  holding requests for {rate_limit[inter]} seconds" )
                    logger.error (f"Server asks for {response.headers['Retry-After']}")
                    time.sleep(rate_limit[inter])
                    return { 'status' : 'KO'}
        else:
            time.sleep (60)
            return { 'status' : 'KO'}
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        logger.error(f"General error: {e}")
        time.sleep (60)
        #raise SystemExit()
    
    logger.debug(response.content.decode('utf-8'))
    return response.json()

#
# Get global blockchain informations
# 
def blockchain_state (validator):
    global current_epoch, current_finalized_epoch, current_slot
    
    API_Data =  api_fetcher_json(endpoint + 'latestState')
    # Print json data using loop 
    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
    if  not 'status' in API_Data or API_Data['status'] != 'KO':
        current_epoch = API_Data['currentEpoch']
        current_finalized_epoch = API_Data['currentFinalizedEpoch']
        current_slot = API_Data['currentSlot']

#
# Validators rewards
#
def validator_reward (validator):
    API_Data =  api_fetcher_json(endpoint + 'validator/' + validator + '/incomedetailhistory?limit=1&latest_epoch=' + str(current_finalized_epoch))
    if  'status' in API_Data and API_Data['status'] == 'OK' and API_Data['data']:
        # Rewards 
        REWARD.labels(validator,'head').set(int(API_Data['data'][0]['income'].get('attestation_head_reward',0)))
        REWARD.labels(validator,'source').set(int(API_Data['data'][0]['income'].get('attestation_source_reward',0)))
        REWARD.labels(validator,'target').set(int(API_Data['data'][0]['income'].get('attestation_target_reward',0)))
        REWARD.labels(validator,'sync').set(int(API_Data['data'][0]['income'].get('sync_committee_reward',0)))
        REWARD.labels(validator,'slashing').set(int(API_Data['data'][0]['income'].get('slashing_reward',0)))
        # Penalties
        PENALTY.labels(validator,'source').set(int(API_Data['data'][0]['income'].get('attestation_target_penalty',0)))
        PENALTY.labels(validator,'target').set(int(API_Data['data'][0]['income'].get('attestation_source_penalty',0)))
        PENALTY.labels(validator,'finality_delay').set(int(API_Data['data'][0]['income'].get('finality_delay_penalty',0)))
        PENALTY.labels(validator,'sync').set(int(API_Data['data'][0]['income'].get('sync_committee_penalty',0)))
        PENALTY.labels(validator,'slashing').set(int(API_Data['data'][0]['income'].get('slashing_penalty',0)))
#
# Gather info about blockchain 
# 
def validator_info (validator):
    """  Collects various data on the blockchain itself  """

    API_Data =  api_fetcher_json(endpoint + 'validator/' + validator )
    if API_Data['status'] == 'OK':
    
        INFO.info ({'status': API_Data['data']['status'] ,
                    'balance': '%.2f' % (API_Data['data']['balance'] / 1000000000),
                    'slashed': str(API_Data['data']['slashed']),
                    'current_epoch': str(current_epoch),
                    'current_slot': str(current_slot),
                    'current_finalized_epoch': str(current_finalized_epoch)
                    })

#
# Validator efficiency (inclusion)
#
def validator_efficiency (validator):
    API_Data =  api_fetcher_json(endpoint + 'validator/' + validator +'/attestationefficiency')
    if 'status' in API_Data and API_Data['status'] == 'OK':
        eff = round(200 -API_Data['data'][0]['attestation_efficiency']*100)
        ATTESTATION_EFFECTIVENESS.labels(validator).set(eff)
    else:
        ATTESTATION_EFFECTIVENESS.labels(validator).set(0)

# 
#  Performance and Rank
# 
def validator_performance (validator):
    API_Data =  api_fetcher_json(endpoint + 'validator/' + validator +'/performance')
    if 'status' in API_Data and API_Data['status'] == 'OK':
        RANK.labels(validator,'7d').set(int(API_Data['data'][0]['rank7d']))
        PERFORMANCE.labels(validator,'1d').set(int(API_Data['data'][0]['performance1d']))
        PERFORMANCE.labels(validator,'7d').set(int(API_Data['data'][0]['performance7d']))
        PERFORMANCE.labels(validator,'31d').set(int(API_Data['data'][0]['performance31d']))
        PERFORMANCE.labels(validator,'365d').set(int(API_Data['data'][0]['performance365d']))

if __name__ == '__main__':
    
    # $$$ tolowercase
    chain = os.getenv('CHAIN', "mainnet")
    validator = os.getenv('VALIDATOR')
    loglevel = os.getenv('LOG', "INFO")
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

    if validator == None:
        logger.error ("Validator ID missing\n")
        help()
        exit(1)
    
    endpoint= 'https://' + chain + '.beaconcha.in/api/v1/'
    logger.info ("Using endpoint %s \n" % (endpoint))
    # Start up the server to expose the metrics.
    start_http_server(8000)

    # Anti restart-hammering endpoint
    time.sleep (20)
    while True:
        process_request(validator)