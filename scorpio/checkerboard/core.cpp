#include <string.h>
#include <Adafruit_NeoPixel.h>
#include <Adafruit_NeoPXL8.h>
#include <SerialUSB.h>
#include "core.h"

extern Adafruit_NeoPXL8 leds;
extern Adafruit_NeoPixel pixel;
extern SerialUSB uart;

void debug(const char *fmt, ...)
{
    static char buf[255];
    va_list args;

    va_start(args, fmt);
    vsnprintf(buf, 1024, fmt, args);
    va_end(args);
    uart.print(buf);
}

void set_rgb(uint8_t red, uint8_t green, uint8_t blue) {
    pixel.setPixelColor(0, pixel.Color(red, green, blue));
    pixel.show();
}

void set_color(color_t *col) {
    pixel.setPixelColor(0, pixel.Color(col->red, col->green, col->blue));
    pixel.show();
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

