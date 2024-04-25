#include <Adafruit_NeoPixel.h>
#include <Adafruit_NeoPXL8.h>
#include <SerialUSB.h>
#include <math.h>
#include "gradient.h"

const uint16_t num_leds = 144;
const uint16_t num_strips = 8;
const uint16_t total_leds = num_leds * num_strips;
const uint16_t total_leds_bytes = total_leds * 3;
const uint16_t bytes_per_row = num_strips * 3;

// For the Feather RP2040 SCORPIO, use this list:
int8_t pins[8] = { 16, 17, 18, 19, 20, 21, 22, 23 };
Adafruit_NeoPXL8 leds(num_leds, pins, NEO_GRB);
Adafruit_NeoPixel pixel(1, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
SerialUSB uart;

color_t rainbow[8] = {
    {255, 0, 0},
    {255, 160, 0},
    {255, 255, 0},
    {0, 255, 63},
    {0, 255, 255},
    {0, 63, 255},
    {127, 0, 255},
    {255, 0, 191}
};

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

    //for(int i = 0; i < 5; i++) {
    //    leds.fill(0xA08000);
    //    leds.show();
    //    delay(100);
    //    leds.fill(0xA000A0);
    //    leds.show();
    //    delay(100);
    //}
    leds.fill(0x0);
    leds.show();

    uart.begin();
    uart.println("trappy!");
}

void show_buffer(color_t data[total_leds]) {
    for(int16_t i = 0; i < num_leds * num_strips; i++)
        leds.setPixelColor(i, leds.Color(data[i].red, data[i].green, data[i].blue));
    leds.show();
}

void set_pixel(color_t buffer[total_leds], uint8_t strip, uint8_t index, color_t * color)
{
    uint16_t offset = (strip * num_leds + index);
    buffer[offset] = *color;
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
    static color_t buffer[total_leds];

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

const uint8_t INWARD = 0;
const uint8_t OUTWARD = 1;

void shift(color_t buffer[total_leds], color_t *new_row, uint8_t direction)
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

void old_chase()
{
    color_t        color, rainbow[num_strips];
    static color_t buffer[total_leds];

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
                memset(buffer, 0, total_leds * 3);
        }    
    }
}

// cool effect to remember set now row to rgb(i,i,i) where monotonically increases
// cool persistence of vision: 

void chase()
{
    color_t buffer[total_leds], new_row[num_strips];

    memset(buffer, 0, total_leds_bytes);
    leds.fill(0x00);
    int stop = millis() + 10000;
    // millis() < stop
    for(int i = 0; ; i++) 
    {
        color_t temp;

        random_color(&temp);
        memset(&new_row, 0, bytes_per_row);
        for(int j = 0; j < num_strips; j++) 
        {
            if (i % 2 == 0)
                new_row[j] = temp; //{(uint8_t)i, 0, (uint8_t)i};
            else
                new_row[j] = {0,0,0};
        }
        shift(buffer, new_row, OUTWARD);
        show_buffer(buffer);
    }
}

void effect_chase()
{
    color_t buffer[total_leds];
    memset(buffer, 32, total_leds_bytes);

    uart.println("in effect chase");
    int stop = millis() + 10000;
    // millis() < stop
    for(int i = 0; ;) 
    {
        i = effect(buffer, i, num_leds, &pattern_every_other);
//        effect(buffer, &pattern_every_other, -num_leds);
    }
}

uint effect(color_t buffer[total_leds], uint row_index, int num_rows, void (*pattern_func)(uint, color_t[num_strips]))
{
    int     direction = (num_rows > 0) ? 1 : 0;
    color_t row[num_strips];
   
    for(int j = 0; j < abs(num_rows); j++, row_index++) 
    {
        (*pattern_func)(row_index, row);
        shift(buffer, row, direction);
        show_buffer(buffer);
    }
    return row_index;
}

void pattern_every_other(uint row, color_t data[num_strips])
{
    if (row % 2 == 0)
        row_random(row, data);
    else
        memset(data, 0, bytes_per_row);
}

void pattern_all(uint row, color_t data[num_strips])
{
    row_rainbow(row, data);
}

void row_rainbow(uint index, color_t col[num_strips])
{
    memcpy(col, rainbow, bytes_per_row);
}

void row_random(uint index, color_t col[num_strips])
{
    color_t color;

    random_color(&color);
    for(int i = 0; i < num_strips; i++)
    {
        col[i].red = color.red;
        col[i].green = color.green;
        col[i].blue = color.blue;        
    }
}

void row_binary(uint index, color_t col[num_strips])
{
    color_t color;

    random_color(&color);
    for(int i; i < num_strips; i++)
    {
        if (index & (1 << i) != 0) {
          col[i].red = 255; //color.red;
          col[i].green = 0; //color.green;
          col[i].blue = 0; //color.blue;        
        }
    }
}

void loop()
{
    effect_chase();
    //gradient_test();
    //checkerboard();
}
