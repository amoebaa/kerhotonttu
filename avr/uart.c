/*
 * CFile1.c
 *
 * Created: 28.9.2014 0:18:03
 *  Author: mikael
 */ 


#include "uart.h"
#include "i2c.h"

struct record {
	char data[5];
};


char date[6] = {0, 0, 0, 0, 0, 0};
static struct record dataRecs[DATA_BUF_SIZE];
static uint8_t rec_tail;
static uint8_t rec_head;
uint8_t recs;


static void (*handleInput)(char);

static void uartFree(char c);

char str[12];

static void waitTx(char c);


//staattinen versio ett‰ k‰‰nt‰j‰ osais optimoida paremmin
static void startTx_() {
	add(&txBuf, '\r');
	add(&txBuf, '\n');
	handleInput = &waitTx;
	UCSRB |= 1 << UDRIE;
}

//aloitetaan l‰hett‰minen
void startTx() {
	startTx_();
}


//bitit 0-5 minuutit, 6-10 tunnit, 11-15 p‰iv‰t,
//16-19 kuukaudet, 20-25 vuosi, 26 ovi, 27 valo,
//32-29 l‰mpˆtila
int addRecord() {
	uint8_t next_head = (rec_head + 1) & (DATA_BUF_SIZE - 1);
	if (next_head == rec_tail) return -1;
	dataRecs[rec_head].data[0] = (date[1] << 2) + (date[2] >> 3);
	dataRecs[rec_head].data[1] = (date[2] << 5) + date[3];
	dataRecs[rec_head].data[2] = (date[4] << 4) + (date[5] >> 2);
	//ovidata on 3. LSB bitiss‰ joten shiftataan vain 3
	dataRecs[rec_head].data[3] = (date[5] << 6) + (ovi << 3) + (valo << 4);
	dataRecs[rec_head].data[4] = lampo;
	rec_head = next_head;
	recs++;
	return 0;
}

//purkaa tallenteen ja muuttaa sen l‰hetett‰v‰ksi stringiksi
int sendRecord() {
	if (recs == 0) return -1;
	txData = 1;
	uint8_t index = rec_tail;
	strncpy(str, "REC,", 12);
	addstr(&txBuf, str);
	itoa(dataRecs[index].data[0] >> 2, str, 10);
	if (strlen(str) == 1) add(&txBuf, '0');
	addstr(&txBuf, str);
	add(&txBuf, ',');
	itoa(((dataRecs[index].data[0] & 0b00000011) << 3) + (dataRecs[index].data[1] >> 5), str, 10);
	if (strlen(str) == 1) add(&txBuf, '0');
	addstr(&txBuf, str);
	add(&txBuf, ',');
	itoa(dataRecs[index].data[1] & 0b00011111, str, 10);
	if (strlen(str) == 1) add(&txBuf, '0');
	addstr(&txBuf, str);
	add(&txBuf, ',');
	itoa(dataRecs[index].data[2] >> 4, str, 10);
	if (strlen(str) == 1) add(&txBuf, '0');
	addstr(&txBuf, str);
	add(&txBuf, ',');
	itoa(((dataRecs[index].data[2] & 0x0F) << 2) + (dataRecs[index].data[3] >> 6), str, 10);
	if (strlen(str) == 1) add(&txBuf, '0');
	addstr(&txBuf, str);
	add(&txBuf, ',');
	itoa(dataRecs[index].data[4], str, 10);
	addstr(&txBuf, str);
	add(&txBuf, ',');
	add(&txBuf, ((dataRecs[index].data[3] & (1<<5))>> 5) + '0');
	add(&txBuf, ',');
	add(&txBuf, ((dataRecs[index].data[3] & (1<<4))>> 4) + '0');
	startTx_();
	
	return 0;
}

//poistetaan tallenne
int removeRec() {
	if (recs == 0) return -1;
	rec_tail = (rec_tail + 1) & (DATA_BUF_SIZE - 1);
	recs--;
	return 0;
}

//tehd‰‰n kahdesta merkist‰ int
static int calcInt(char c1, char c2) {
	char temp[3] = "  ";
	temp[0] = c1;
	temp[1] = c2;
	return atoi(temp);
}

//k‰sitell‰‰n vastaanotettu kellonaika
static void receiveTime() {
	const int maxdays[12] = {31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
	int sec;
	int min;
	int hour;
	int day;
	int month;
	int year;
	if (elements(&rxBuf) != 12) {
		empty(&rxBuf);
		return;
	}
	for (uint8_t i = 0; i < 12; i++) {
		str[i] = remove(&rxBuf);
	}
	sec = calcInt(str[0], str[1]);
	min = calcInt(str[2], str[3]);
	hour = calcInt(str[4], str[5]);
	day = calcInt(str[6], str[7]);
	month = calcInt(str[8], str[9]);
	year = calcInt(str[10], str[11]);
	//tarkistetaan onko oikean suuruisia
	if (sec < 60 && min < 60 && hour < 24 && month > 0 && month < 13 &&
	  day > 0 && day <= maxdays[month - 1] && year < 64 /**&& !i2cOn**/) {
		date[0] = sec;
		date[1] = min;
		date[2] = hour;
		date[3] = day;
		date[4] = month;
		date[5] = year;
		i2ctxBuf[0] = 0x00;
		i2ctxBuf[1] = ((str[0] - '0') << 4) + (str[1] - '0');
		i2ctxBuf[2] = ((str[2] - '0') << 4) + (str[3] - '0');
		i2ctxBuf[3] = ((str[4] - '0') << 4) + (str[5] - '0');
		i2ctxBuf[4] = 0x01;
		i2ctxBuf[5] = ((str[6] - '0') << 4) + (str[7] - '0');
		i2ctxBuf[6] = ((str[8] - '0') << 4) + (str[9] - '0');
		i2ctxBuf[7] = ((str[10] - '0') << 4) + (str[11] - '0');
		setTime();
	}
	else {
		strncpy(str, "error", 8);
		addstr(&txBuf, str);
		startTx_();
	}
}

//odotetaan ajan vastaanottoa
void waitRx(char c) {
	//jos otettu vastaan v‰‰r‰ m‰‰r‰ aikadataa, nollataan vastaanotto
	if ((c != ENDCHAR && (elements(&rxBuf) > 12 || !isdigit(c)))  || (c == ENDCHAR && elements(&rxBuf) != 12)) {
		while(elements(&rxBuf) > 0) {
			add(&txBuf, remove(&rxBuf));
		}
		startTx_();
	}
	else if (c == ENDCHAR) {
		receiveTime();
		handleInput = &uartFree;
	}
	else {
		add(&rxBuf, c);	
	}
}

//odotetaan l‰hetyst‰
void waitTx(char c) {
	//do nothing
}

void waitAck(char c) {
	//odotetaan kuittausta datasta, jos saadaan se,
	//poistetaan tallenne
	if (c == ACKCHAR) {
		removeRec();
		if (recs > 0) {
			handleInput = &waitTx;
			sendRecord();
		}
		else {
			strncpy(str, "empty", 12);
			addstr(&txBuf, str);
			txData = 0;
			startTx_();
		}
	}
	else {
		handleInput = &uartFree;
		txData = 0;
		txOn = 0;
	}
}

static void uartFree(char c) {
	//asetetaan aika
	if (c == 'A') {
		handleInput = &waitRx;
	}
	//kysyt‰‰n oven tilaa
	else if (c == 'O') {
		if (ovi) strncpy(str, "auki", 12);
		else strncpy(str, "kiinni", 12);
		addstr(&txBuf, str);
		startTx_();
	}
	//kysyt‰‰n l‰mpˆtilaa
	else if (c ==  'L') {
		itoa(lampo, str, 10);
		addstr(&txBuf, str);
		startTx_();
	}
	//pyydet‰‰n dataa
	else if (c == 'D') {
		if (sendRecord() == -1) {
			strncpy(str, "empty", 12);
			addstr(&txBuf, str);
			startTx_();
		}
	}
	//kysyt‰‰n valon tilaa
	else if (c == 'V') {
		if (valo) strncpy(str, "valo", 12);
		else strncpy(str, "valo pois", 12);
		addstr(&txBuf, str);
		startTx_();
	}
	//pyydet‰‰n aika
	else if (c == 'T') {
		for (uint8_t i = 0; i < 6; i++) {
			itoa(date[i], str, 10);
			addstr(&txBuf, str);
			add(&txBuf, ',');
		}
		startTx_();
	}
}

void uart_init() {
	UBRRL = 142;
	UCSRA |= (1<<U2X);
	UCSRC |= (1<<URSEL) | (1<<UCSZ0) | (1<<UCSZ1) | (1<<UPM1);
	UCSRB |= (1<<RXCIE) | (1<<RXEN) | (1<<TXEN);
	
	init_buf(&txBuf, TX_BUF_SIZE, txBuf_array);
	init_buf(&rxBuf, RX_BUF_SIZE, rxBuf_array);
	
	ovi = 0;
	lampo = 0;
	valo = 0;
		
	recs = 0;
	rec_head = 0;
	rec_tail = 0;

	handleInput = &uartFree;
}

ISR(USART_RXC_vect) {
	//USART vastaanotto valmis
	if (UCSRA & ((1<<FE) | (1<<PE))) {
		add(&txBuf, 'E');
		add(&txBuf, UDR);
		startTx_();
	}
	else handleInput(UDR);
}

ISR(USART_UDRE_vect) {
	//USART puskuri tyhj‰
	if (elements(&txBuf) > 0) {
		UDR = remove(&txBuf);
	}
	//l‰hetys valmis
	else {
		if (txData) handleInput = &waitAck;
		else {
			handleInput = &uartFree;
			txOn = 0;
		}
		UCSRB &= ~(1 << UDRIE);
	}
}