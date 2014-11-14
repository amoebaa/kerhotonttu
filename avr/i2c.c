/*
 * CFile1.c
 *
 * Created: 29.9.2014 22:57:49
 *  Author: mikael
 */ 

#define I2ADDR 0b11010000

#include "i2c.h"


static void (*handleI2C)();

static uint8_t index;

//virheenk‰sittely
static void error(char c) {
	//jotain virheenk‰sittely‰?
	char temp[3] = "  ";
	itoa (TWSR, temp, 16);
	add(&txBuf, c);
	add(&txBuf, ':');
	addstr(&txBuf, temp);
	add(&txBuf, ' ');
	startTx();
}

//initialisointi
void i2c_init() {
	TWBR = 16;
	TWSR = 0b11111000;
	handleI2C = 0;
}

//l‰hett‰‰ datan slaven osoitteeseen
static void sendData() {
	if ((TWSR & 0b11111000) != 0x18 && (TWSR & 0b11111000) != 0x28) error('2');
	else if (index < 8) {
		TWDR = i2ctxBuf[index];
		index++;
		TWCR = 0b10000101;
	}
	else {
		i2cOn = 0;
		handleI2C = 0;
		TWCR = 0b10000000; 
	}
}

//kirjoittaa slaven osoitteen
static void sendAddr_w() {
	if ((TWSR & 0b11111000) != 0x08) error('1');
	TWDR = I2ADDR;
	handleI2C = sendData;
	TWCR = 0b10000101;
}

//asetetaan aika, aloitetaan aloitusmerkill‰
int setTime() {
	if (i2cOn) return -1;
	handleI2C = sendAddr_w;
	i2cOn = 1;
	index = 0;
	TWCR = 0b10100101;
	return 0;
}

//lukee dataa, kun luettu asettaa p‰iv‰m‰‰r‰n ja sammuttaa v‰yl‰n
static void getData() {
	if ((TWSR & 0b11111000 )!= 0x40 && (TWSR & 0b11111000 )!= 0x50) error('7');
	if (index < 8) {
		if (index != 0) i2crxBuf[index - 1] = TWDR;
		TWCR = 0b11000101;
		index++;
	}
	else {
		handleI2C = 0;
		TWCR = 0b10000000;
		i2cOn = 0;
		date[0] = ((i2crxBuf[0] & 0xF0) >> 1) + ((i2crxBuf[0] & 0xF0) >> 3) + (i2crxBuf[0] & 0x0F);
		date[1] = ((i2crxBuf[1] & 0xF0) >> 1) + ((i2crxBuf[1] & 0xF0) >> 3) + (i2crxBuf[1] & 0x0F);
		date[2] = ((i2crxBuf[2] & 0xF0) >> 1) + ((i2crxBuf[2] & 0xF0) >> 3) + (i2crxBuf[2] & 0x0F);
		date[3] = ((i2crxBuf[4] & 0xF0) >> 1) + ((i2crxBuf[4] & 0xF0) >> 3) + (i2crxBuf[4] & 0x0F);
		date[4] = ((i2crxBuf[5] & 0xF0) >> 1) + ((i2crxBuf[5] & 0xF0) >> 3) + (i2crxBuf[5] & 0x0F);
		date[5] = ((i2crxBuf[6] & 0xF0) >> 1) + ((i2crxBuf[6] & 0xF0) >> 3) + (i2crxBuf[6] & 0x0F);
	}
}

//aloittaa datan lukemisen
static void startRead() {
	if ((TWSR & 0b11111000) != 0x10) error('6');
	handleI2C = getData;
	TWDR = I2ADDR + 0x01;
	TWCR = 0b10000101;
}

//l‰hett‰‰ toistetun aloitusmerkin
static void sendRepStart() {
	if ((TWSR & 0b11111000) != 0x28) error('5');
	handleI2C = startRead;
	TWCR = 0b10100101;
}

//tutkii oliko virheit‰, ja l‰hett‰‰ slaven muistin osoitteen
static void sendAddr_p() {
	if ((TWSR & 0b11111000) != 0x18) error('4');
	handleI2C = sendRepStart;
	TWDR = 0x00;
	TWCR = 0b10000101;
}

//tutkii oliko virheit‰, ja l‰hett‰‰ slaven osoitteen
static void sendAddr_r() {
	if ((TWSR & 0b11111000) != 0x08) error('3');
	handleI2C = sendAddr_p;
	TWDR = I2ADDR;
	TWCR = 0b10000101;
}

//hakee ajan reaaliaikakellolta, laittaa I2C startin p‰‰lle
int getTime() {
	if (i2cOn) return -1;
	handleI2C = sendAddr_r;
	i2cOn = 1;
	index = 0;
	TWCR = 0b10100101;
	return 0;
}

//kutsutaan funktiota jossa oikeasti k‰sitell‰‰n keskeytys
ISR(TWI_vect) {
	if (handleI2C != 0) handleI2C();
}


