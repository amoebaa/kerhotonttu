/*
 * IncFile1.h
 *
 * Created: 28.9.2014 0:18:36
 *  Author: mikael
 */ 


#ifndef UART_H
#define UART_H

#include <avr/io.h>
#include <avr/interrupt.h>
#include <inttypes.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

#include "ringbuf.h"

#define ENDCHAR '\r'
#define ACKCHAR 'K'
#define RX_BUF_SIZE 16
#define TX_BUF_SIZE 32
#define DATA_BUF_SIZE 128

char date[6];
char date_aux[6];
	
volatile uint8_t ovi;
uint8_t lampo;
uint8_t valo;
int txData;
int txOn;
int16_t audiospl;

char txBuf_array[TX_BUF_SIZE];
char rxBuf_array[RX_BUF_SIZE];

struct ringBuffer txBuf;
struct ringBuffer rxBuf;

int addRecord();

int sendRecord();

int removeRec();


void uart_init();
void startTx();




#endif /* INCFILE1_H_ */