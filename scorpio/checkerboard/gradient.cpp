#include <stdio.h>
#include <SerialUSB.h>
#include "gradient.h"

#define min(a,b)  (((a) < (b)) ? (a) : (b))

extern SerialUSB uart;

void gradient_color(gradient_t *grad, uint16_t led, color_t *dest) 
{
    float offset;

    if (led > grad->leds)
        return;

    offset = led / (float)grad->leds;
    uart.print(offset);
    uart.print(" ");
    uart.println(led);
    for(int index = 1; index < grad->points; index++) {
        if (grad->palette[index].index >= offset) {
            float   section_begin_offset = grad->palette[index - 1].index;
            float   section_end_offset = grad->palette[index].index;
            int16_t red, green, blue;

            float percent = (offset - section_begin_offset) / (section_end_offset - section_begin_offset);
            red = (int)(grad->palette[index - 1].color.red +
                  ((grad->palette[index].color.red - grad->palette[index - 1].color.red) * percent));
            green = (int)(grad->palette[index - 1].color.green +
                    ((grad->palette[index].color.green - grad->palette[index - 1].color.green) * percent));
            blue = (int)(grad->palette[index - 1].color.blue +
                   ((grad->palette[index].color.blue - grad->palette[index - 1].color.blue) * percent));

            dest->red = min(red, 255);
            dest->green = min(green, 255);
            dest->blue = min(blue, 255);
        }
    }
}
