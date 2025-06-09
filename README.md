# Swarm Dashboard

This is a small project using Python to manage Docker Swarm services through a web UI.

The dashboard displays the services of each stack on each worker node, the status and replicas of each service, allows updating services, and shows service logs.

## How to

Git clone the repository and run it on a management node of the Docker Swarm cluster.

### Build image

```
docker build -t swarm-dashboard .
```
### Run image
```
docker run -d -p 5000:5000 \
  -e DASHBOARD_USERNAME=admin \
  -e DASHBOARD_PASSWORD=xxxx \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --name swarm-dashboard \
  swarm-dashboard
```
