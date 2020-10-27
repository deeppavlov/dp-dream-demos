
## harvesters_status + harvester status + prepare_trip 
* all_statuses_request
    - utter_all_statuses_request
* status_request
    - utter_status_request
* trip_request
    - utter_trip_request


## harvesters_status + broken ids  
* all_statuses_request
    - utter_all_statuses_request
* broken_ids_request
    - utter_broken_ids_request

## harvesters_status + full_ids_request  
* all_statuses_request
    - utter_all_statuses_request
* full_ids_request
    - utter_full_ids_request

## harvesters_status + working_ids_request  
* all_statuses_request
    - utter_all_statuses_request
* working_ids_request
    - utter_working_ids_request

## harvesters_status + inactive_ids_request
* all_statuses_request
    - utter_all_statuses_request
* inactive_ids_request{"rovers_inactive" : "yes", "inactive_rover_ids" : "2"}
    - utter_inactive_ids_request

## harvesters_status + inactive_ids_request
* all_statuses_request
    - utter_all_statuses_request
* inactive_ids_request{"rovers_inactive" : "yes", "inactive_rover_ids" : "2"}
    - utter_inactive_ids_request

## available_rovers + prepare_trip
* available_rover_ids_request
    - utter_available_rover_ids_request
* trip_request{"rovers_available" : "yes", "rovers" : "1"}
    - utter_trip_request

## available_rovers + prepare_trip failed
* available_rover_ids_request
    - utter_available_rover_ids_request
* trip_request{"rovers_available" : "no"}
    - utter_trip_request_failed

## available_rovers + no_broken_rover_ids_request
* available_rover_ids_request
    - utter_available_rover_ids_request
* broken_rover_ids_request{"rovers_broken" : "no"}
    - utter_broken_rover_ids_request

## available_rovers + broken_rover_ids_request
* available_rover_ids_request
    - utter_available_rover_ids_request
* broken_rover_ids_request{"rovers_broken" : "yes", "broken_rover_ids" : 2}
    - utter_broken_rover_ids_request

## available_rovers + no_inactive_rover_ids_request
* available_rover_ids_request
    - utter_available_rover_ids_request
* inactive_rover_ids_request{"rovers_inactive" : "no"}
    - utter_no_inactive_rover_ids_request

## available_rovers + inactive_rover_ids_request
* available_rover_ids_request
    - utter_available_rover_ids_request
* inactive_rover_ids_request{"rovers_inactive" : "yes", "inactive_rover_ids" : 3}
    - utter_inactive_rover_ids_request