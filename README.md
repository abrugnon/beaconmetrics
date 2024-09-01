# beaconmetrics

expose beaconcha.in validator API results as prometheus metrics


## Beaconcha.in API documentation

(https://holesky.beaconcha.in/api/v1/docs/index.html)




## Building and running container 

docker run --rm  -e CHAIN=holesky  -e VALIDATOR=123456 -p 8000:8000 beaconmetrics
curl http://localhost:8000 


## Public docker image 

docker run --rm  -e CHAIN=holesky  -e VALIDATOR=123456 -p 8000:8000 ghcr.io/abrugnon/beaconmetrics:release

## Parameters

- LOG
- CHAIN
- VALIDATOR

## Exported Data

-  HELP validator_rank Rank among validators - 1 day sliding
   # TYPE validator_rank gauge
   validator_rank{range="7d",validator="1662052"}
-  HELP validator_performance Performance
   # TYPE validator_performance gauge
   validator_performance{range=...,validator=...}
-  HELP validator_effectiveness Attestation effectiveness percentage
   # TYPE validator_effectiveness gauge
   validator_effectiveness{validator=...} 91.0
-  HELP validator_reward Rewards for actions
   # TYPE validator_reward gauge
   validator_reward{type=...,validator=...} ...

-   HELP validator_penalty Penalty for actions
# TYPE validator_penalty gauge
validator_penalty{type="source",validator="1662052"} 0.0
validator_penalty{type="target",validator="1662052"} 0.0
validator_penalty{type="finality_delay",validator="1662052"} 0.0
validator_penalty{type="sync",validator="1662052"} 0.0
validator_penalty{type="slashing",validator="1662052"} 0.0

