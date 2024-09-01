from prometheus_client import start_http_server,  Summary, Gauge,  Counter, Info
import time
import os
import requests
import logging

# Create metrics.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
ATTESTATION_EFFECTIVENESS = Gauge("validator_effectiveness" , 'Attestation effectiveness percentage',['validator'])
RANK = Gauge("validator_rank" , 'Rank among validators - 1 day sliding',['validator','range'])
PERFORMANCE = Gauge("validator_performance" , 'Performance',['validator','range'])
REWARD = Gauge("validator_reward" , 'Rewards for actions',['validator','type'])
PENALTY = Gauge("validator_penalty" , 'Penalty for actions',['validator','type'])

INFO = Info('validator_status' ,'Information about on-chain validator')


# initial settings
current_epoch = 0
current_finalized_epoch = 0
current_slot = 0

logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

INFO.info ({'status': 'unknown' })


#
# request scheduler
#
def process_request(validator):
    """A dummy function that takes some time."""
    blockchain_state (validator)
    time.sleep(15)
    validator_performance (validator)
    time.sleep(15)
    validator_efficiency (validator)
    time.sleep(11)
    validator_info (validator)
    time.sleep(15)
    validator_reward(validator)
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
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        print ("Connection error")
        raise SystemExit(e)
    
    logger.debug(response.headers)

    # Content -> Too Many Requests
    # Limit headers X-Ratelimit-Remaining-Month / Day / Hour / Minute / Second
    for inter in rate_limit.keys ():
        if (response.headers['X-Ratelimit-Remaining-' + inter]) == '0':
            logger.error("Limit reached (" + inter + "):  holding requests for " +  str( rate_limit[inter]) + " seconds" )
            break 

    logger.debug(response.content.decode('utf-8'))
    if response.content == b"Too Many Requests\n" :

        logger.error("API endpoint Rate limited exceeded\n")
        return { 'status' : 'KO'}

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
    # response = requests.get(endpoint + 'validator/' + validator + '/incomedetailhistory?limit=1&latest_epoch=' + str(current_finalized_epoch))
    # API_Data = response.json()
    API_Data =  api_fetcher_json(endpoint + 'validator/' + validator + '/incomedetailhistory?limit=1&latest_epoch=' + str(current_finalized_epoch))
    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
    #print (API_Data['data'][0])
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
# Gather info about blockchain 
# 

def validator_info (validator):
    """  Collects various data on the blockchain itself  """

    API_Data =  api_fetcher_json(endpoint + 'validator/' + validator )
    # Print json data using loop 
    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
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
    # Print json data using loop 
    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
    if 'status' in API_Data and API_Data['status'] == 'OK':
        eff = round(200 -API_Data['data'][0]['attestation_efficiency']*100)
        #print ('eff:' + str(eff))
        ATTESTATION_EFFECTIVENESS.labels(validator).set(eff)
        # ATTESTATION_EFFECTIVENESS.set(eff)
    else:
        ATTESTATION_EFFECTIVENESS.set(None)

# 
#  Performance and Rank
# 
def validator_performance (validator):
    API_Data =  api_fetcher_json(endpoint + 'validator/' + validator +'/performance')
    # Print json data using loop 
    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
    if 'status' in API_Data and API_Data['status'] == 'OK':

        RANK.labels(validator,'7d').set(int(API_Data['data'][0]['rank7d']))
        #print ('eff:' + str(eff))
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
    
    while True:
        process_request(validator)