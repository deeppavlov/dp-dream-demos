# Simple Dream AI Demo with Single Go-Bot-powered Goal-Oriented Skill

It consists of one goal-oriented kill powered by Go-Bot from DeepPavlov.

Runs with docker-compose

## Key Files

* **docker-compose.yml** - includes all services required to run this demo
* **/agent/pipeline_conf.json** - DeepPavlov Agent pipeline configuration file
* **/agent/db_conf.json** - db configuration, which works with docker-compose provided
* **/skills/harvesters_maintenance_gobot_skill/** - actual goal-oriented skill powered by Go-Bot from DeepPavlov.
* **/skills/harvesters_maintenance_gobot_skill/dp_minimal_demo_dir** - put the output of Go-Bot tutorial in here

## Requirements

* [Docker](https://www.docker.com/products/docker-desktop) 
* [Docker-compose](https://docs.docker.com/compose/install/)

## Running the demo

```bash
docker-compose up --build
```

Api will run on *localhost:4242/*

All dialogs will be saved in **dp-agent** database, running in **mongo** container.
