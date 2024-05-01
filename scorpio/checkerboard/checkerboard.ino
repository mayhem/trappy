
#include <SerialUSB.h>
#include <math.h>
#include <Adafruit_NeoPixel.h>
#include <Adafruit_NeoPXL8.h>
#include "defs.h"
#include "core.h"
#include "gradient.h"
#include "scroller.h"
#include "color.h"

// For the Feather RP2040 SCORPIO, use this list:
int8_t pins[8] = { 16, 17, 18, 19, 20, 21, 22, 23 };
Adafruit_NeoPXL8 leds(num_leds, pins, NEO_GRB);
Adafruit_NeoPixel pixel(1, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
SerialUSB uart;

void setup() {
    randomSeed(68);

    pixel.begin();   
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
    for(int i = 0; i < 3; i++)
    {
        set_rgb(255, 120, 0);
        leds.fill(0xA08000);
        leds.show();
        delay(100);
        set_rgb(255, 0, 255);
        leds.fill(0xA000A0);
        leds.show();
        delay(100);
    }
    set_rgb(0, 0, 0); 

    leds.fill(0x0);
    leds.show();

    uart.begin();
}

void checkerboard() {
    static uint8_t i = 0;
    static color_t buffer[total_leds];
    color_t        color;
  
    int stop = millis() + 10000;
    while(millis() < stop) {
      memset(buffer, 0, total_leds_bytes);
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

void gradient_test()
{
    gradient_t     grad;
    color_t        color;
    static color_t buffer[total_leds];

    grad.points = 3;
    grad.leds = 144;
    grad.palette[0].index = 0.0;
    grad.palette[0].color = {255, 0, 0};
    grad.palette[1].index = .5;
    grad.palette[1].color = {255, 0, 255};
    grad.palette[2].index = 1.0;
    grad.palette[2].color = {255, 120, 0};

    //random_color(&grad.palette[0].color);
    //random_color(&grad.palette[1].color);
    //random_color(&grad.palette[2].color);

    for(float t = 0.0; t < 100; t+=.1) {
        float wiggle = (sin(t/8) / 8.0) + .5 + (sin(t*3) / 12);
        grad.palette[1].index = wiggle;
        for(int j = 0; j < num_leds; j++) { 
            for(int k = 0; k < num_strips; k++) {
                gradient_color(&grad, (float)j / num_leds, &color);
                set_pixel(buffer, k, j, &color);
            }
        }
        show_buffer(buffer); 
    }
   
}

void effect_chase()
{
    color_t buffer[total_leds];
    memset(buffer, 32, total_leds_bytes);
    effect_t eff;

    eff.pattern_fptr = &pattern_every_other;
    eff.row_fptr = &row_matrix;
    eff.palette.points = 2;
    eff.palette.palette[0].index = 0.0;
    eff.palette.palette[0].color = {255, 0, 0};
    eff.palette.palette[1].index = 1.0;
    eff.palette.palette[1].color = {255, 0, 255};
  
    int stop = millis() + 10000;
    for(int i = 0;millis() < stop ;) 
    {
        i = scroll(&eff, buffer, i, num_leds);
        i = scroll(&eff, buffer, i, -num_leds);
    }
}


void loop()
{
    effect_chase();
    //gradient_test();
    //checkerboard();
}
