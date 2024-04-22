#include <Adafruit_NeoPixel.h>
#include <Adafruit_NeoPXL8.h>
#include <SerialUSB.h>
#include "gradient.h"

const uint16_t num_leds = 144;
const uint16_t num_strips = 8;
const uint16_t buffer_size = num_leds * num_strips * 3;

// For the Feather RP2040 SCORPIO, use this list:
int8_t pins[8] = { 16, 17, 18, 19, 20, 21, 22, 23 };
Adafruit_NeoPXL8 leds(num_leds, pins, NEO_GRB);
Adafruit_NeoPixel pixel(1, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
SerialUSB uart;

void gradient_test();

void set_color(uint8_t red, uint8_t green, uint8_t blue) {
    pixel.setPixelColor(0, pixel.Color(red, green, blue));
    pixel.show();
}

void setup() {
    uart.begin();
    pixel.begin();
    set_color(0, 0, 0);
    if (!leds.begin()) {
        for(;;)
        {
            set_color(255, 0, 0);
            delay(100);
            set_color(0, 0, 0);
            delay(100);
        }
    }
    leds.setBrightness(64);
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

void show_buffer(uint8_t *data) {
    for(int16_t i = 0; i < num_leds * num_strips; i++)
        leds.setPixelColor(i, leds.Color(data[i * 3], data[i*3+1], data[i*3+2]));
    leds.show();
}

void set_pixel(uint8_t *buffer, uint8_t strip, uint8_t index, color_t * color)
{
    uint16_t offset = (strip * num_leds + index) * 3;
    buffer[offset] = color->red;
    buffer[offset + 1] = color->green;
    buffer[offset + 2] = color->blue;
}

void checkerboard() {
    static uint8_t i = 0;
    static uint8_t buffer[buffer_size];
    color_t        color;
  
    memset(buffer, 0, buffer_size);
    for(int j = 0; j < num_strips; j++) {
        for(int k = 0; k < num_leds; k++) {
          if (k / 4 % 2 == (i % 2))
              color = { 255, 0, 0 };
          else
              color = { 255, 0, 255 };
          set_pixel(buffer, j, k, &color);
        }
    }
    i++;
    
    show_buffer(buffer); 
}

void gradient_color(gradient_t *grad, uint16_t led, color_t *dest);
void gradient_test()
{
    gradient_t grad;
    color_t    color;
    static uint8_t buffer[buffer_size];

    grad.points = 2;
    grad.leds = 144;
    grad.palette[0].index = 0.0;
    grad.palette[0].color = {255, 0, 0};
    grad.palette[1].index = .5;
    grad.palette[1].color = {255, 80, 0};
    //grad.palette[2].index = 1.0;
    //grad.palette[2].color = {255, 0, 255};

    for(int j = 0; j < num_strips; j++) {
        for(int k = 0; k < num_leds; k++) {
            delay(250);
            gradient_color(&grad, k, &color);
            set_pixel(buffer, j, k, &color);
        }
    }
    show_buffer(buffer); 
}

void loop()
{
    checkerboard();
}
