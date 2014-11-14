/*
 * IncFile1.h
 *
 * Created: 29.9.2014 22:53:14
 *  Author: mikael
 */ 


#ifndef I2C
#define I2C


#include <inttypes.h>
#include <avr/io.h>

#include "uart.h"


char i2ctxBuf[8];
char i2crxBuf[7];

uint8_t i2cOn;

void i2c_init();

int getTime();

int setTime();


#endif /* INCFILE1_H_ */