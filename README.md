# Challenges of the course "Internet Of Things" - Politecnico di Milano
## What's in this repo
This repository contains the solution to the challenges of the year 2023.
## How to reproduce the results
### Challenge 1
Simply download the pcap, export it with wireshark, put it in the git folder, and run the notebook.
### Challenge 2
Import the flow in node-red, and set up a channel where you send ids. To send IDs the suggestion is to use [MQTT-Explorer](http://mqtt-explorer.com/), and send them just with an ID in the JSON format:
```
{
    "id" = <NUMBER>
}
```
