/* Dieser Sketch dient dem Auslesen der relativen x- und y-Verschiebung des optischen ADNS2610 Chips
 * 
 * 
 */


#include <ADNS2610.h> 



/*Arduino Pinbelegung, siehe Board */
#define     SCK_PIN             2 /* Clock Pin */
#define     SDIO_PIN            3 /* Data In&Out Pin */

using namespace ADNS2610;


/* setze Absolutwerte (x,y) auf 0 */
long int x = 0;
long int y = 0;

/*erzeuge Sensorobjekt */
Sensor opticalSensor( SCK_PIN, SDIO_PIN );


void setup() {
    /* definiere Baudrate: Symbole/s */
    Serial.begin( 250000 );

    /* schalte LED dauerhaft ein */
    opticalSensor.SetAwakeLED();
    
    /* Initalisierung */
    delay(1000);
}



/* Hauptprogramm */

void loop() {

    /* lese Relativverschiebung (dx, dy) aus Register */
    /* Reihenfolge NICHT ändern */
    signed char dy = opticalSensor.GetDY();
    signed char dx = opticalSensor.GetDX();


    /* ermittle Absolutwerte (x, y) */
    y += int(dy);    
    x += int(dx);

    
  
    /********************************************************/
    /* ES DARF NUR EINE SERIAL.PRINT()-ANSICHT AKTIV SEIN */
    /********************************************************/


    /* bereite Daten für das Auslesen vor (Python) */
    /* Schreibe alle Variablen in 1 Zeile */
    Serial.print(dx, DEC);
    Serial.print("t");

    Serial.print(dy, DEC);
    Serial.print("t");

    Serial.print("end");
    Serial.println();
    



    /* Plotansicht mit Grenzen -128 bis +127 */
    /*
    Serial.print(127);
    Serial.print(" ");
    Serial.print(-128);
    Serial.print(" ");
    Serial.println(dy, DEC);
    //Serial.print(" ");
    //Serial.println(dx, DEC);
    */



    
    /*Plotansicht dy, y, dx, x */
    /*    
    //y-Verschiebung
    Serial.print(" ");
    Serial.print(dy, DEC);
    Serial.print(" ");

    //y-Absolut
    Serial.print(y);
    Serial.print(" ");
  
    
    //x-Verschiebung
    Serial.print(dx, DEC);
    Serial.print(" ");

    //x-Absolut
    Serial.print(x);
    Serial.println();
    */
    
}
