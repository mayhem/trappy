#include <stdlib.h>

#include "color.h"

void random_color(color_t *col)
{
    col->red = (int)(rand() * 128) + 127;
    col->green = (int)(rand() * 128) + 127;
    col->blue = (int)(rand() * 128) + 127;
}
