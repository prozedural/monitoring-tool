/* Dieser Sketch dient dem Auslesen des Sensorbildes des optischen ADNS2610 Chips
 * 
 * 
 */

#include <ADNS2610.h> 

/*Arduino Pinbelegung, siehe Board */
#define     SCK_PIN             2 /* Clock Pin */
#define     SDIO_PIN            3 /* Data In&Out Pin */

using namespace ADNS2610;

int i = 0;

/*erzeuge Sensorobjekt */
Sensor opticalSensor( SCK_PIN, SDIO_PIN );





void setup() {
    /* schalte LED dauerhaft ein */
    opticalSensor.SetAwakeLED();

    /* definiere Baudrate: Symbole/s */
    Serial.begin( 250000 );
    
    /* Initalisierung */
    delay(1000);
}



/* Hauptprogramm */

void loop() {
    uint8_t* frame = new uint8_t;

    /* gib Anzahl der gelesenen Pixel zurück */
    uint16_t nP = opticalSensor.GetImage( frame );

    /* lese Pixelwerte aus Register */
    for( uint16_t i = 0; i < nP; i++ ) {

        /* erzeuge exakt eine Zeile mit allen Pixelwerten */
        Serial.print( frame[ i ] );

        /* trenne alle Einzelwerte durch Separator zum Auslesen via PySerial */
        Serial.print(",");
      }

    i++;
    /* füge einen weiteren Separator ein */
    Serial.print("end");
    /* Zeilenumbruch nach einem Frame */
    Serial.println();

    /* lösche den Framebuffer */
    delete frame;
}
