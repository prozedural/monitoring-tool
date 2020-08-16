#include "ADNS2610.h"

namespace ADNS2610
{
    /*Protected methods*/
    void Sensor::SetAddress( uint8_t address, DataDirection direction ) const
    {
        pinMode( sdioPin, OUTPUT );
    
        /*Specify data direction:
         *MSB = 0   ===>   read operation
         *MSB = 1   ===>   write operation*/
        switch( direction )
        {
            case( TO_SENSOR ) :
                address |= 0b10000000 ;
                break;
            case( FROM_SENSOR ) :
                address &= ~0b10000000 ;
                break;
        }
    
        for( uint8_t mask = 0b10000000; mask; mask >>= 1 )
        {
            digitalWrite( sckPin, HIGH );
            digitalWrite( sckPin, LOW );
            digitalWrite( sdioPin, address & mask );
            digitalWrite( sckPin, HIGH );
        }
        /*It's not necessary to wait for 100 us
         *because digitalWrite takes a lot of time itself*/
         delayMicroseconds( 100 );
    
        /*Set SDIO pin in High-Z state
         *( see p.13 in the datasheet )*/
         pinMode( sdioPin, INPUT );
    }
    
    
    uint8_t Sensor::ReadRegister( uint8_t address ) const
    {
        SetAddress( address, FROM_SENSOR );
    
        uint8_t data = 0b00000000;
    
        /*Read data from a register*/
        pinMode( sdioPin, INPUT );
        for( uint8_t mask = 0b10000000; mask; mask >>= 1 )
        {
            digitalWrite( sckPin, HIGH );
            digitalWrite( sckPin, LOW );
            digitalWrite( sckPin, HIGH );
    
            if( digitalRead( sdioPin ) )
            {
                data |= mask;
            }
        }
    
        /*Wait for 0.25 microseconds between read and either
         *read or write operations (see p.15 of the datasheet)*/
        delayMicroseconds( 1 ); /*changed from 1 to 100 */
    
        return data;
    }
    
    
    void Sensor::WriteRegister( uint8_t address, uint8_t data ) const
    {
        SetAddress( address, TO_SENSOR );
    
        pinMode( sdioPin, OUTPUT );
        /*Write data to a register*/
        for( uint8_t mask = 0b10000000; mask; mask >>= 1 )
        {
            digitalWrite( sckPin, HIGH );
            digitalWrite( sckPin, LOW );
            digitalWrite( sdioPin, data & mask );
            digitalWrite( sckPin, HIGH );
        }
        /*It's not necessary to wait for 100 us
         *because digitalWrite takes a lot of time itself*/
        delayMicroseconds( 100 );
    }
    
    
    void Sensor::SetConfigBit( uint8_t bit, bool state ) const
    {
        uint8_t currentState = ReadRegister( CFG_REG_ADDR );
    
        if( state )
        {
            currentState |= ( 1 << bit );
        }
        else
        {
            currentState &= ~( 1 << bit );
        }
    
        WriteRegister( CFG_REG_ADDR, currentState );
    }
    

    /*Public methods*/
    bool Sensor::IsAwake() const
    {
        //Returns the status of the LED
        return ReadRegister( STS_REG_ADDR ) & 0b00000001;
    }
    
    
    signed char Sensor::GetDX() const
    {
        //Returns x-shift
        return (signed char)ReadRegister( DX_REG_ADDR );
    }
    
    
    signed char Sensor::GetDY() const
    {
        //Returns y-shift
        return (signed char)ReadRegister( DY_REG_ADDR );
    }
    
    
    uint8_t Sensor::GetSQUAL() const
    {
        //Returns number of features in the frame
        //SetAwakeLED();
    
        return ReadRegister( SQL_REG_ADDR ) * 2;
    
        //SetNormalLED();
    }
    
    uint8_t Sensor::GetMaxPixel() const
    {
        //Returns maximum pixel value in the frame
        //SetAwakeLED();
    
        return ReadRegister( MXP_REG_ADDR ) & 0b00111111;
    
        //SetNormalLED();
    }
    
    
    uint8_t Sensor::GetMinPixel() const
    {
        //Returns minimum pixel value in the frame
        //SetAwakeLED();
    
        return ReadRegister( MNP_REG_ADDR ) & 0b00111111;
    
        //SetNormalLED();
    }
    
    
    uint8_t Sensor::GetPixelAverage() const
    {
        //Returns average of the pixel values
    //    SetAwakeLED();
    
        return ReadRegister( PXLSUM_REG_ADDR ) * 0.395;
    }
    
    
    uint16_t Sensor::GetImage( uint8_t* frame ) const
    {
    
        //Returns number of pixels have been read
        SetAwakeLED();
    
        /*Write anything to pixel data register
         *( see p.23 in the datasheet)*/
        WriteRegister( PXLDAT_REG_ADDR, 0x00 );
    
        uint16_t nPixelsRead = 0;//Monitor how many pixels were read
        while( true )
        {
            uint8_t pixelData = ReadRegister( PXLDAT_REG_ADDR );    
            /*Continue reading only if there is valid data
             *(see p.23 in the datasheet)*/
            if( pixelData & ( 1 << PXLDAT_REG_VLD ) )
            {
                /*Check if this is start of framm (see p.23 in the datasheet)*/
                if( pixelData & ( 1 << PXLDAT_REG_SOF ) )
                {
                    /*The first pixel*/
                    if( !nPixelsRead )
                    {
                        frame[ nPixelsRead++ ] = pixelData & 0b00111111 ;
                    }
                    else
                    {
                        return nPixelsRead;
                    }
                }
                else
                {
                    frame[ nPixelsRead++ ] = pixelData & 0b00111111 ;
                }
            }
        }
    }
    
    
    void Sensor::SetAwakeLED() const
    {
        //Sets LED in "always awake" mode
        SetConfigBit( CFG_REG_LED, 1 );
    }
    
    
    void Sensor::SetNormalLED() const
    {
        //Sets LED in normal mode
        SetConfigBit( CFG_REG_LED, 0 );
    }
}//ADNS2610
