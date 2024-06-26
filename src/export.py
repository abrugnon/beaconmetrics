from prometheus_client import start_http_server,  Summary, Gauge,  Counter, Info
import time
import os
import requests

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

INFO.info ({'status': 'unknown' })



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



# Decorate function with metric.
@REQUEST_TIME.time()
def blockchain_state (validator):
    global current_epoch, current_finalized_epoch, current_slot
    response = requests.get( endpoint + 'latestState' )
    API_Data = response.json()
    # Print json data using loop 
    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
    current_epoch = API_Data['currentEpoch']
    current_finalized_epoch = API_Data['currentFinalizedEpoch']
    current_slot = API_Data['currentSlot']


#
# Validators rewards
#
@REQUEST_TIME.time()
def validator_reward (validator):
    response = requests.get(endpoint + 'validator/' + validator + '/incomedetailhistory?limit=1&latest_epoch=' + str(current_finalized_epoch))
    API_Data = response.json()

    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
    #print (API_Data['data'][0])
    if API_Data['status'] == 'OK' and API_Data['data']:
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
@REQUEST_TIME.time()
def validator_info (validator):
    response = requests.get(endpoint + 'validator/' + validator )
    API_Data = response.json()
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
@REQUEST_TIME.time()
def validator_efficiency (validator):
    response = requests.get(endpoint + 'validator/' + validator +'/attestationefficiency')
    API_Data = response.json()
    # Print json data using loop 
    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
    if API_Data['status'] == 'OK':
        eff = round(200 -API_Data['data'][0]['attestation_efficiency']*100)
        #print ('eff:' + str(eff))
        ATTESTATION_EFFECTIVENESS.labels(validator).set(eff)
        # ATTESTATION_EFFECTIVENESS.set(eff)
    else:
        ATTESTATION_EFFECTIVENESS.set(None)

# 
#  Performance and Rank
# 
@REQUEST_TIME.time()
def validator_performance (validator):
    response = requests.get(endpoint + 'validator/' + validator +'/performance')
    API_Data = response.json()
    # Print json data using loop 
    # for key in API_Data:{ 
    #     print(key,":", API_Data[key]) 
    # }
    if API_Data['status'] == 'OK':

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

    if validator == None:
        print ("Validator ID missing\n")
        help()
        exit(1)
    
    endpoint= 'https://' + chain + '.beaconcha.in/api/v1/'
    print ("Using endpoint %s \n" % (endpoint))
    # Start up the server to expose the metrics.
    start_http_server(8000)
    
    while True:

        process_request(validator)