

#ifndef RADIO_ROUTE_H
#define RADIO_ROUTE_H


// Message type
/*
|       Type      |    src    |     dest     |     data     |
-------------------------------------------------------------
|     DATA_MSG    | sender id | receiver id  |     data     |
|  ROUTE_REQ_MSG  |     0     |      0       | requested id |
| ROUTE_REPLY_MSG | sender id | requested id |     cost     |
*/
typedef nx_struct radio_route_msg {
	nx_uint8_t type;
	nx_uint16_t src;
	nx_uint16_t dest;
	nx_uint16_t data; 
} radio_route_msg_t;

enum {
	DATA_MSG = 0,
	ROUTE_REQ_MSG = 1,
	ROUTE_REPLY_MSG = 2,
};

enum {
  AM_RADIO_COUNT_MSG = 10,
};

#endif
