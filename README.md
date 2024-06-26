# beaconmetrics
expose beaconcha.in validator API results as prometheus metrics


## Beaconcha.in API documentation

(https://holesky.beaconcha.in/api/v1/docs/index.html)




## Building and running container 

docker run --rm  -e CHAIN=holesky  -e VALIDATOR=123456 -p 8000:8000 beaconmetrics
curl http://localhost:8000 