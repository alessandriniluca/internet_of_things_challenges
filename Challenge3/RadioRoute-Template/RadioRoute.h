

#ifndef RADIO_ROUTE_H
#define RADIO_ROUTE_H


// Message types
typedef nx_struct radio_route_msg {
	nx_uint8_t type;
	nx_uint16_t src; //sender id
	nx_uint16_t dest; // receiver id or node requsted
	nx_uint16_t data; // data or cost
} radio_route_msg_t;

enum {
  AM_RADIO_COUNT_MSG = 10,
};

#endif
