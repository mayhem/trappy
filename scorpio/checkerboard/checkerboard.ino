#include <Adafruit_NeoPixel.h>
#include <Adafruit_NeoPXL8.h>
#include <SerialUSB.h>
#include <math.h>
#include "gradient.h"

const uint16_t num_leds = 144;
const uint16_t num_strips = 8;
const uint16_t buffer_size = num_leds * num_strips;

// For the Feather RP2040 SCORPIO, use this list:
int8_t pins[8] = { 16, 17, 18, 19, 20, 21, 22, 23 };
Adafruit_NeoPXL8 leds(num_leds, pins, NEO_GRB);
Adafruit_NeoPixel pixel(1, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
SerialUSB uart;

void gradient_test();

void set_rgb(uint8_t red, uint8_t green, uint8_t blue) {
    pixel.setPixelColor(0, pixel.Color(red, green, blue));
    pixel.show();
}

void set_color(color_t *col) {
    pixel.setPixelColor(0, pixel.Color(col->red, col->green, col->blue));
    pixel.show();
}

void setup() {
    randomSeed(68);
    uart.begin();
    pixel.begin();
    set_rgb(0, 0, 0);
    if (!leds.begin()) {
        for(;;)
        {
            set_rgb(255, 0, 0);
            delay(100);
            set_rgb(0, 0, 0);
            delay(100);
        }
    }
    leds.setBrightness(10);
    for(int i = 0; i < 5; i++) {
        leds.fill(0xFF9000);
        leds.show();
        delay(100);
        leds.fill(0xFF00FF);
        leds.show();
        delay(100);
    }
    leds.fill(0x0);
    leds.show();
}

void show_buffer(color_t *data) {
    for(int16_t i = 0; i < num_leds * num_strips; i++)
        leds.setPixelColor(i, leds.Color(data[i].red, data[i].green, data[i].blue));
    leds.show();
}

void set_pixel(color_t *buffer, uint8_t strip, uint8_t index, color_t * color)
{
    uint16_t offset = (strip * num_leds + index);
    buffer[offset] = *color;
}

void hue_to_color(byte pos, color_t *col) 
{
    if(pos < 42) {
        *col = { (uint8_t)(pos * 6), (uint8_t)(255 - pos * 6), 0 };
    } else if(pos < 85) {
        pos -= 42;
        *col = { (uint8_t)(255 - pos * 6), 0, (uint8_t)(pos * 6) };
    } else if (pos < 127) {
        pos -= 85;
        *col = {0, (uint8_t)(pos * 6), (uint8_t)(255 - pos * 6) };
    } else if (pos < 169) {
        pos -= 127;
        *col = { (uint8_t)(pos * 6), (uint8_t)(255 - pos * 6), (uint8_t)(pos * 3) };
    } else if (pos < 211){
        pos -= 169;
        *col = { (uint8_t)(255 - pos * 6), (uint8_t)(pos * 3), (uint8_t)(pos * 6) };
    } else {
        pos -= 211;
        *col = { (uint8_t)(pos * 3), (uint8_t)(pos * 6), (uint8_t)(255 - pos * 6) };
    }  
}

float fract(float x) { return x - int(x); }

float mix(float a, float b, float t) { return a + (b - a) * t; }

float step(float e, float x) { return x < e ? 0.0 : 1.0; }

void hsv2rgb(float h, float s, float b, color_t *col) {
  col->red = (uint8_t )(b * mix(1.0, constrain(abs(fract(h + 1.0) * 6.0 - 3.0) - 1.0, 0.0, 1.0), s));
  col->green = (uint8_t )(b * mix(1.0, constrain(abs(fract(h + 0.6666666) * 6.0 - 3.0) - 1.0, 0.0, 1.0), s));
  col->blue = (uint8_t )(b * mix(1.0, constrain(abs(fract(h + 0.3333333) * 6.0 - 3.0) - 1.0, 0.0, 1.0), s));
}

void checkerboard() {
    static uint8_t i = 0;
    static color_t buffer[buffer_size];
    color_t        color;
  
    int stop = millis() + 10000;
    while(millis() < stop) {
      memset(buffer, 0, buffer_size * 3);
      for(int j = 0; j < num_strips; j++) {
          for(int k = 0; k < num_leds; k++) {
            if (k / 4 % 2 == (i % 2))
                color = { 255, 0, 0 };
            else
                color = { 0, 0, 255 };
            set_pixel(buffer, j, k, &color);
          }
      }
      i++;
      show_buffer(buffer); 
    }
}

void random_color(color_t *col)
{
    col->red = (int)(rand() * 128) + 127;
    col->green = (int)(rand() * 128) + 127;
    col->blue = (int)(rand() * 128) + 127;
}

void gradient_test()
{
    gradient_t     grad;
    color_t        color;
    static color_t buffer[buffer_size];

    grad.points = 3;
    grad.leds = 144;
    grad.palette[0].index = 0.0;
    //grad.palette[0].color = {255, 0, 0};
    grad.palette[1].index = .5;
    //grad.palette[1].color = {255, 255, 0};
    grad.palette[2].index = 1.0;
    //grad.palette[2].color = {0, 255, 0};

    random_color(&grad.palette[0].color);
    random_color(&grad.palette[1].color);
    random_color(&grad.palette[2].color);

    for(float t = 0.0; t < 100; t+=.1) {
        float wiggle = (sin(t) / 6.0) + .5 + (sin(t*4) / 12);
        grad.palette[1].index = wiggle;
        for(int j = 0; j < num_leds; j++) {
            //gradient_color(&grad, j, &color);   
            for(int k = 0; k < num_strips; k++) {
                gradient_color(&grad, j, &color);
                set_pixel(buffer, k, j, &color);
            }
        }
        show_buffer(buffer); 
    }
   
}

const uint8_t OUTWARD = 0;
const uint8_t INWARD = 1;

void shift(color_t *buffer, color_t *new_row, uint8_t direction)
{
    for(int i = 0; i < num_strips; i++)
    {
        if (direction == INWARD)
        {
            color_t *ptr = buffer + (i * num_leds);
            for(int j = 0; j < num_leds - 1; j++)
            {
                *ptr = *(ptr + 1);
                ptr++;
            }
            *ptr = new_row[i];
        }
        else
        {
            color_t *ptr = buffer + (i * num_leds) + (num_leds - 1);
            for(int j = 0; j < num_leds - 1; j++)
            {
                *ptr = *(ptr - 1);
                ptr--;
            }
            *ptr = new_row[i];
        }
    }
}

// cool effect to remember set now row to rgb(i,i,i) where monotonically increases
// cool persistence of vision: 

void new_chase()
{
    color_t buffer[num_strips * num_leds], new_row[num_strips];

    memset(buffer, 0, buffer_size * 3);
    leds.fill(0x00);
    int stop = millis() + 10000;
    // millis() < stop
    for(int i = 0; ; i++) 
    {
        color_t temp;

        random_color(&temp);
        memset(&new_row, 0, sizeof(color_t) * 8);
        for(int j = 0; j < num_strips; j++) 
        {
            if (i % 2 == 0)
                new_row[j] = temp;
        }
        shift(buffer, new_row, OUTWARD);
        show_buffer(buffer);
    }
}

void chase()
{
    color_t        color, rainbow[num_strips];
    static color_t buffer[buffer_size];

    for(int i = 0; i < 8; i++) {
        //hsv2rgb(i * 0.125, 1.0, 1.0,  &rainbow[i]);
        random_color(&rainbow[i]);
    }
 
    for(int i = 0; i < 10; i++) {
        int clear = i % 3 == 0;
        for(int j = 0; j < num_leds; j++) {
            for(int k = 0; k < num_strips; k++) {
                set_pixel(buffer, k, j, &rainbow[k]);
            }
            show_buffer(buffer);

            if (clear)
                memset(buffer, 0, buffer_size * 3);
        }    
    }
}

void loop()
{
    new_chase();
    //gradient_test();
    //checkerboard();
}
