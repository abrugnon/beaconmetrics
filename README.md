# beaconmetrics

expose beaconcha.in validator API results as prometheus metrics


## Beaconcha.in API documentation

[beaconcha.in](https://holesky.beaconcha.in/api/v1/docs/index.html 'docs')

## Building and running container 
```
docker build -t beaconmetrics .
docker run --rm  -e CHAIN=holesky  -e VALIDATOR=123456 -p 8000:8000 beaconmetrics
# test with 
curl http://localhost:8000 
```
## Public docker image 

```docker run --rm  e LOG=DEBUG -e CHAIN=holesky  -e VALIDATOR=123456 -p 8000:8000 ghcr.io/abrugnon/beaconmetrics:release```

## Parameters

- LOG
- CHAIN
- VALIDATOR

## Exported Data

-  HELP validator_rank Rank among validators - 1 day sliding
   TYPE validator_rank gauge
   ```validator_rank{range="7d",validator="1662052"}```
-  HELP validator_performance Performance
   TYPE validator_performance gauge
   ```validator_performance{range=...,validator=...}```
-  HELP validator_effectiveness Attestation effectiveness percentage
   TYPE validator_effectiveness gauge
   ```validator_effectiveness{validator=...} xx.xx```
-  HELP validator_reward Rewards for actions
   TYPE validator_reward gauge
   ```validator_reward{type=...,validator=...} ...```
-  HELP validator_penalty Penalty for actions
   TYPE validator_penalty gauge
   ```validator_penalty{type="source",validator="...."} x.x```


