#ifndef __CORE_H__
#define __CORE_H__

#include <stdarg.h>
#include "defs.h"

void debug(const char *fmt, ...);

void set_rgb(uint8_t red, uint8_t green, uint8_t blue);
void set_color(color_t *col);
void show_buffer(color_t data[total_leds]);
void set_pixel(color_t buffer[total_leds], uint8_t strip, uint8_t index, color_t * color);

#endif
