#ifndef ADNS2610_H
#define ADNS2610_H

#include <inttypes.h>

#include <Arduino.h>

namespace ADNS2610
{
    //Addresses of the registers
    const uint8_t     CFG_REG_ADDR      = 0x00;//Config register
    const uint8_t     STS_REG_ADDR      = 0x01;//Status register
    const uint8_t     DY_REG_ADDR       = 0x02;//Delta y register
    const uint8_t     DX_REG_ADDR       = 0x03;//Delta x register
    const uint8_t     SQL_REG_ADDR      = 0x04;//SQUAL register
    const uint8_t     MXP_REG_ADDR      = 0x05;//Max pixel register
    const uint8_t     MNP_REG_ADDR      = 0x06;//Min pixel register
    const uint8_t     PXLSUM_REG_ADDR   = 0x07;//Pixel's sum register
    const uint8_t     PXLDAT_REG_ADDR   = 0x08;//Pixel data register
    const uint8_t     STRUPR_REG_ADDR   = 0x09;//Shutter upper register
    const uint8_t     STRLWR_REG_ADDR   = 0x0A;//Shutter lower register
    const uint8_t     INVPRD_REG_ADDR   = 0x0B;//Inverse product code register
    
    //Bits of the configuration register
    const uint8_t     CFG_REG_LED       = 0x00;//LED control bit
    const uint8_t     CFG_REG_PWRDWN    = 0x06;//Power down bit
    const uint8_t     CFG_REG_RST       = 0x07;//Reset config bit
    
    //Bits of the Pixel data register
    const uint8_t     PXLDAT_REG_VLD    = 0x06;//Valid data bit
    const uint8_t     PXLDAT_REG_SOF    = 0x07;//Start of frame bit
    
    //Auxiliaries
    const uint16_t    N_PIXELS          = 324;//Sensor's resolution in pixels
    const uint8_t     N_ROWS            = 18;
    const uint8_t     N_COLUMNS         = 18;


    /*A sensor is represented by this class*/
    class Sensor 
    {
        protected :
            uint8_t         sckPin;//clock pin
            uint8_t         sdioPin;//data in/output pin 
            enum            DataDirection { TO_SENSOR, FROM_SENSOR };

            void            SetAddress( uint8_t address, DataDirection direction ) const;
            uint8_t         ReadRegister( uint8_t address ) const;
            void            WriteRegister( uint8_t address, uint8_t data ) const;
            void            SetConfigBit( uint8_t bit, bool state ) const;
    
        public :
            Sensor( uint8_t sckPin, uint8_t sdioPin ) :
                sckPin( sckPin ),
                sdioPin( sdioPin )
            {
                pinMode( sckPin, OUTPUT );
                pinMode( sdioPin, INPUT );
            }
    
            bool            IsAwake( ) const;
            signed char     GetDX( ) const;
            signed char     GetDY( ) const;
            uint8_t         GetSQUAL( ) const;
            uint8_t         GetMaxPixel( ) const;
            uint8_t         GetMinPixel( ) const;
            uint8_t         GetPixelAverage( ) const;
            uint16_t        GetImage( uint8_t* frame ) const;
    
            void            SetAwakeLED() const;
            void            SetNormalLED() const;
    };//Sensor
}//ADNS2610
#endif
