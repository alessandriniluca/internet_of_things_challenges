
/*
*	IMPORTANT:
*	The code will be avaluated based on:
*		Code design  
*
*/
 
 
#include "Timer.h"
#include "RadioRoute.h"
//#include <lib/hashmap.h>


module RadioRouteC @safe() {
  uses {
  
    /****** INTERFACES *****/
	interface Boot;
  interface Leds;
  interface Receive;
  interface AMSend;
  interface Timer<TMilli> as Timer0;
  interface Timer<TMilli> as Timer1;
  interface SplitControl as AMControl;
  interface Packet;


    //interfaces for communication
	//interface for timers
	//interface for LED
    //other interfaces, if needed
  }
}
implementation {

  message_t packet;
  
  // Variables to store the message to send
  message_t queued_packet;
  uint16_t queue_addr;
  uint16_t time_delays[7]={61,173,267,371,479,583,689}; //Time delay in milli seconds

  //Array to store the routing table
  typedef struct routing_table_row {
    uint16_t next_hop; // ID del prossimo hop
    uint16_t cost; // costo del percorso
  } routing_table_row_t;

  routing_table_row_t routing_table[7];
  

  message_t my_queued_packet;
  uint16_t my_queue_addr;
  
  bool route_req_sent=FALSE;
  bool route_rep_sent=FALSE;
  
  bool locked;
  
  bool actual_send (uint16_t address, message_t* packet);
  bool generate_send (uint16_t address, message_t* packet, uint8_t type);

  
  
  bool generate_send (uint16_t address, message_t* packet, uint8_t type){
    /*
    * 
    * Function to be used when performing the send after the receive message event.
    * It store the packet and address into a global variable and start the timer execution to schedule the send.
    * It allow the sending of only one message for each REQ and REP type
    * @Input:
    *		address: packet destination address
    *		packet: full packet to be sent (Not only Payload)
    *		type: payload message type
    *
    * MANDATORY: DO NOT MODIFY THIS FUNCTION
    */
  	if (call Timer0.isRunning()){
  		return FALSE;
  	}else{
      if (type == 1 && !route_req_sent ){
        route_req_sent = TRUE;
        call Timer0.startOneShot( time_delays[TOS_NODE_ID-1] );
        queued_packet = *packet;
        queue_addr = address; //modified because of typo
      }else if (type == 2 && !route_rep_sent){
        route_rep_sent = TRUE;
        call Timer0.startOneShot( time_delays[TOS_NODE_ID-1] );
        queued_packet = *packet;
        queue_addr = address; //modified because of typo
      }else if (type == 0){
        call Timer0.startOneShot( time_delays[TOS_NODE_ID-1] );
        queued_packet = *packet;
        queue_addr = address; //modified because of typo
      }
  	}
  	return TRUE;
  }
  
  event void Timer0.fired() {
  	/*
  	* Timer triggered to perform the send.
  	* MANDATORY: DO NOT MODIFY THIS FUNCTION
  	*/
  	actual_send (queue_addr, &queued_packet);
  }
  
  bool actual_send (uint16_t address, message_t* packet){
    /*
    * Implement here the logic to perform the actual send of the packet using the tinyOS interfaces
    */
    if (locked){
      dbg("radio_send","locked!!!\n");
      return FALSE;
    }else{
      
      radio_route_msg_t* msg = (radio_route_msg_t*)call Packet.getPayload(packet, sizeof(radio_route_msg_t));
      dbg("radio_send","Sending packet of type %u to %u with data: %u\n", msg->type, address, msg->data);
      if (call AMSend.send(address, packet, sizeof(radio_route_msg_t)) == SUCCESS){
        locked = TRUE;
        return TRUE;
      }
      return FALSE;
    }
  }
  
  
  event void Boot.booted() {
    uint16_t i;
    for (i = 0; i < 7; i++) {
      routing_table[i].cost = 0;
    }

    dbg("boot","Application booted.\n");
    /* Fill it ... */
    
    call AMControl.start();
  }

  event void AMControl.startDone(error_t err) {
    /* Fill it ... */
    if (err == SUCCESS) {
      call Timer1.startOneShot(5000);
      call Timer1.startOneShot(5000);
    }
    else {
      call AMControl.start();
    }
  }

  event void AMControl.stopDone(error_t err) {
    /* Fill it ... */
  }
  
  event void Timer1.fired() {
    /*
    * Implement here the logic to trigger the Node 1 to send the first REQ packet
    */
    dbg("timer","Timer1 fired.\n");
    if (TOS_NODE_ID == 1){
      if(routing_table[6].cost == 0){
        radio_route_msg_t* sendMsg = (radio_route_msg_t*)call Packet.getPayload(&packet, sizeof(radio_route_msg_t));
        sendMsg->type = 1;//REQ
        sendMsg->data = 7;
        dbg("timer","Sending REQ to %d\n", sendMsg->data);
        generate_send(AM_BROADCAST_ADDR, &packet, 1);
        call Timer1.startOneShot(1000); //TODO check
      }else{
        radio_route_msg_t* sendMsg = (radio_route_msg_t*)call Packet.getPayload(&packet, sizeof(radio_route_msg_t));
        sendMsg->type = 0;
        sendMsg->src = TOS_NODE_ID;
        sendMsg->dest = 7;
        sendMsg->data = 5;
        dbg("timer","Sending DATA to %d\n", routing_table[6].next_hop);
        generate_send(routing_table[6].next_hop, &packet, 0);
      }
    }
  
  }

  event message_t* Receive.receive(message_t* bufPtr, void* payload, uint8_t len) {
    /*
    * Parse the receive packet.
    * Implement all the functionalities
    * Perform the packet send using the generate_send function if needed
    * Implement the LED logic and print LED status on Debug
    */
    
    
    if(len == sizeof(radio_route_msg_t)){
      radio_route_msg_t* recMsg = (radio_route_msg_t*)payload;
      dbg("radio_rec","Received packet of type %u with data: %u\n", recMsg->type, recMsg->data);
      if(recMsg->type == 0){//data
        if(recMsg->dest == TOS_NODE_ID){// if the packet is for me
          //TODO
          dbg("radio_rec","data received: %d\n", recMsg->data);
        }else{
          if (routing_table[recMsg->dest-1].cost == 0){
            //send ROUTE_REQ to all 
            //should not happen
            //TODO check
            dbg("radio_rec","routing table not complete\n");
            //my_queued_packet = payload;
            //my_queue_addr = recMsg->dest;
            //packet.type = 1;
            //packet.data = recMsg->dest;
            //call generate_send(AM_BROADCAST_ADDR, &packet, 1);
            //Timer1.startOneShot(100);
          }else{
            //send data to next hop
           
            radio_route_msg_t* sendMsg = (radio_route_msg_t*)call Packet.getPayload(&packet, sizeof(radio_route_msg_t));
            sendMsg->type = 0;
            sendMsg->src = recMsg->src;
            sendMsg->dest = recMsg->dest;
            sendMsg->data = recMsg->data;
            dbg("timer","Forwarding DATA to %d\n", routing_table[6].next_hop);
            generate_send(routing_table[recMsg->dest-1].next_hop, &packet, 0);
          }
        }

      }else if(recMsg->type == 1){//ROUTE_REQ
      
        radio_route_msg_t* sendMsg = (radio_route_msg_t*)call Packet.getPayload(&packet, sizeof(radio_route_msg_t));
        if(recMsg->data == TOS_NODE_ID){// if the packet is for me
          //send back ROUTE_REPLY with cost 1
          sendMsg->type = 2;
          sendMsg->src = TOS_NODE_ID; //sender
          sendMsg->dest = TOS_NODE_ID; //node requested
          sendMsg->data = 1;
          generate_send(AM_BROADCAST_ADDR, &packet, 2);
        }else{
          if (routing_table[recMsg->dest-1].cost == 0){ // if I have not that entry, I need to broadcast it
            //send ROUTE_REQ to all
            dbg("radio_send","Preparing ROUTE_REQ to all for finding node %d\n", recMsg->data);
            sendMsg->type = 1;
            sendMsg->data = recMsg->data; //REQUESTED NODE
            generate_send(AM_BROADCAST_ADDR, &packet, 1);
          }else{
            //send ROUTE_REPLY to all incrementing the cost 
            sendMsg->type = 2;
            sendMsg->src = TOS_NODE_ID; //sender
            sendMsg->dest = recMsg->data; //node requested
            sendMsg->data = routing_table[recMsg->data - 1].cost + 1;
            generate_send(AM_BROADCAST_ADDR, &packet, 2);
          }
        }
      }else if(recMsg->type == 2){//ROUTE_REPLY

        radio_route_msg_t* sendMsg = (radio_route_msg_t*)call Packet.getPayload(&packet, sizeof(radio_route_msg_t));
        if(recMsg->dest != TOS_NODE_ID){
          if (routing_table[recMsg->dest-1].cost == 0){
            routing_table[recMsg->dest-1].cost = recMsg->data;
            routing_table[recMsg->dest-1].next_hop = recMsg->src;
            sendMsg->type = 2;
            sendMsg->src = TOS_NODE_ID;
            sendMsg->dest = recMsg->dest;
            sendMsg->data = recMsg->data + 1;
            generate_send(AM_BROADCAST_ADDR, &packet, 2);
          }else{
            if (routing_table[recMsg->dest-1].cost > recMsg->data){
              routing_table[recMsg->dest-1].cost = recMsg->data;
              routing_table[recMsg->dest-1].next_hop = recMsg->src;
              sendMsg->type = 2;
              sendMsg->src = TOS_NODE_ID;
              sendMsg->dest = recMsg->dest;
              sendMsg->data = recMsg->data + 1;
              generate_send(AM_BROADCAST_ADDR, &packet, 2);
            }
          }
        }
      } 
    }else{
      dbg("radio_rec","Received packet of wrong size\n");
    }
    return bufPtr;
  }

  event void AMSend.sendDone(message_t* bufPtr, error_t error) {
	/* This event is triggered when a message is sent 
	*  Check if the packet is sent 
	*/ 
    locked = FALSE;
    dbg ("radio_send", "Packet sent\n");
  }
}
/*
1 2 -60.0
2 1 -60.0
1 3 -60.0
3 1 -60.0
2 4 -60.0
4 2 -60.0
3 5 -60.0
5 3 -60.0
4 6 -60.0
6 4 -60.0
3 4 -60.0
4 3 -60.0
5 6 -60.0
6 5 -60.0
6 7 -60.0
7 6 -60.0
5 7 -60.0
7 5 -60.0
*/