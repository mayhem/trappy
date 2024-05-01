#include <math.h>
#include <string.h>
#include "scroller.h"
#include "core.h"
#include "color.h"

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

void pattern_every_other(effect_t *eff, unsigned int row, color_t data[num_strips])
{
    if (row % 2 == 0)
        (*eff->row_fptr)(eff, row, data);
    else
        memset(data, 0, bytes_per_row);
}

void pattern_all(effect_t *eff, unsigned int row, color_t data[num_strips])
{
    (*eff->row_fptr)(eff, row, data);
}

void row_rainbow(effect_t *eff, unsigned int index, color_t col[num_strips])
{
    memcpy(col, rainbow, bytes_per_row);
}

void row_random(effect_t *eff, unsigned int index, color_t col[num_strips])
{
    color_t color;
    static unsigned int r = 0;

    //gradient_color(&eff->palette, rand(), &color);
    random_color(&color);
    for(int i = 0; i < num_strips; i++)
    {
        col[i].red = color.red;
        col[i].green = color.green;
        col[i].blue = color.blue;        
    }
    r++;
}

void row_binary(effect_t *eff, unsigned int index, color_t col[num_strips])
{
    color_t color;

    color.red = 255;
    color.green = 80;
    color.blue = 0;

    for(int i = 0; i < num_strips; i++)
    {
        if ((index & (1 << i)) != 0)
        {
            col[i].red = color.red;
            col[i].green = color.green;
            col[i].blue = color.blue;        
        }
        else
        {
            col[i].red = 0;
            col[i].green = 0;
            col[i].blue = 0;  
        }
    }
}

void shift(effect_t *eff, unsigned int index, color_t buffer[total_leds], color_t *new_row, uint8_t direction)
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


unsigned int scroll(effect_t *eff, color_t buffer[total_leds], unsigned int row_index, int num_rows)
{
    int     direction = (num_rows > 0) ? 1 : 0;
    color_t row[num_strips];
   
    for(int j = 0; j < abs(num_rows); j++, row_index++) 
    {
        (*eff->pattern_fptr)(eff, row_index, row);
        shift(eff, row_index, buffer, row, direction);
        show_buffer(buffer);
    }
    return row_index;
}
