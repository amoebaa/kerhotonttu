/*
 * GccApplication2.c
 *
 * Created: 21.9.2014 18:45:20
 *  Author: mikael
 */ 

#ifndef F_CPU
#define F_CPU 11000000 
#endif

#include <avr/io.h>
#include <avr/interrupt.h>

#include <inttypes.h>
#include <util/delay.h>
#include <stdio.h>

#include "i2c.h"
#include "uart.h"

//0. bitti oven tila, 1. bitti edellisell‰ kierroksella luettu tila
//3. bitti kertoo onko oven tila muuttunut mutta ei voitu l‰hett‰‰
//viesti‰ t‰st‰
volatile uint8_t valo_mitt;
volatile uint8_t ovi_edell;
volatile uint8_t ovi_muutos;

int16_t audiospl = 0;
int16_t audiorms = 0;


static void init() {
	
	valo_mitt = 0;
	i2c_init();
	uart_init();

	
	//asetetaan timeri
	OCR1A = 10742;
	PORTC |= 1<<PINC2;
	TCCR1B |= (1<<CS12) | (1<<CS10) | (1<<WGM12);
	
	TIMSK |= 1<<OCIE1A;
	
	txData = 0;
	ADMUX |= 1<<REFS0;
	ADCSRA = (1<<ADEN) | (1<<ADIE) | (1<<ADPS2);
	
	
	sei();
}

int main(void) {
	
	init();
	

    while(1)
    {
		
    }
}



ISR(ADC_vect) {
	if (valo_mitt) {
		int16_t temp = ADC;
		if (temp < 950) valo = 1;
		else valo = 0;
	}
	else {
		int16_t temp = ADC;
		lampo = temp >> 1;
	}
}

ISR(TIMER1_COMPA_vect)  {
	char str[15];
	static uint8_t count = 0;
	
	//h‰ss‰k‰ss‰ tutkitaan onko ovipinnintila sama kuin edellisell‰ kierroksella,
	//jos se on sama, mutta eri kuin oven tilaa kuvaava arvo, oven tila muuttui
	//jos tila muuttuu, mutta on l‰hetys p‰‰ll‰, pistet‰‰n muistiin ett‰ tila muuttui
	//ja aloitetaan kohta uudestaan
	
	//t‰ss‰ kohtaa testataan onko oven tila muuttunut ilman ett‰ tilan muutosta on
	//voitu l‰hett‰‰, jos n‰in on, yritet‰‰n l‰hett‰‰ uudestaan jos UART vapaa
	if (ovi_muutos) {
		if (!txOn && ovi) {
			strncpy(str, "ovi aukesi", 12);
			addstr(&txBuf, str);
			startTx();
			ovi_muutos = 0;
		}
		else if (!txOn && !ovi) {
			strncpy(str, "ovi sulkeutui", 12);
			addstr(&txBuf, str);
			startTx();
			ovi_muutos = 0;		
		}
	}
	//tutkitaan onko oven tila muuttunut, jos on, yritet‰‰n l‰hett‰‰ tieto muutoksesta
	else if ((ovi_edell == (PINC & (1 << PINC2))) && (ovi_edell != ovi)) {
		ovi = ovi_edell;
		if (txOn) ovi_muutos = 1;
		else if (ovi) {
			strncpy(str, "ovi aukesi", 12);
			addstr(&txBuf, str);
			startTx();
			ovi_muutos = 0;			
		}
		else {
			strncpy(str, "ovi sulkeutui", 15);
			addstr(&txBuf, str);
			startTx();
			ovi_muutos = 0;			
		}
	}
	ovi_edell = PINC & (1 << PINC2);
	
	if (valo_mitt) {
		ADMUX &= ~(1<<MUX0);
		valo_mitt = 0;
	}
	else {
		ADMUX |= 1<<MUX0;
		valo_mitt = 1;
	}
	_delay_us(30);
	ADCSRA |= 1<<ADSC;
	getTime();
	//T‰nne esim. sekunneittain tai isommin aikav‰lein teht‰v‰t jutut
	if (count == 60) {
		addRecord();
		count = 0;
	}
	count++;
}
