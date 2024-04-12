#include <Adafruit_NeoPixel.h>
#include <Adafruit_NeoPXL8.h>
#include <SerialUSB.h>

const uint8_t num_leds = 144;
const uint8_t num_strips = 8;
const uint8_t buffer_size = num_leds * num_strips * 3;

// For the Feather RP2040 SCORPIO, use this list:
int8_t pins[8] = { 16, 17, 18, 19, 20, 21, 22, 23 };
Adafruit_NeoPXL8 leds(num_leds, pins, NEO_GRB);
Adafruit_NeoPixel pixel(1, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
SerialUSB uart;

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

void handle_frame(uint8_t *data) {
    for(int i = 0; i < num_leds * num_strips; i++)
        leds.setPixelColor(i, leds.Color(data[i * 3], data[i*3+1], data[i*3+2]));
    leds.show();
}

void handle_show() {
    leds.show();  
}

void handle_clear() {
    leds.fill(0);
    leds.show();  
}

void test() {
    static int i = 0;
    static uint8_t *buffer = (uint8_t*)malloc(buffer_size);
  
    for(int j = 0; j < num_leds * num_strips; j++) {
        buffer[j * 3] = i % 255;
        buffer[j * 3 + 1] = 0;
        buffer[j * 3 + 2] = 80;
    }
  
    handle_frame(buffer);
    i++;
    if (i > 255)
        i = 0;
    leds.fill(0);
    leds.show();  
}

void toggle_led(void) {
    static uint8_t i = 0;

    if (i == 0) {
        i = 1;
        set_color(255, 0, 0);
    }
    else {
        i = 0;
        set_color(0, 0, 0);      
    }
}

void loop()
{
    uint8_t header = 0, ch;
    for(;;)
    {
        header = 0;
        for(;;) {
            ch = uart.read();
            if (ch == 'A')
            {
                header++;
                continue;
            }
            if (header == 1 && ch == 'B')
                break;

            header = 0;
        }
        ch = uart.read();
        if (ch != '1' && ch != '2' && ch != '3') {
            uart.write('0');
            continue;
        }
        if (ch == '1') {
            uint8_t data[num_leds * num_strips * 3];
            uint16_t offset = 0;

            for(;;) {
                uint16_t read = uart.readBytes(data + offset, 1);
                if (read > 0) {
                    offset += read;
                    if (offset == buffer_size)
                        break;
                    continue;
                }
                // If we got a timeout, restart
                if (read == 0) {
                    break;
                }
            }

            handle_frame(data);
            uart.write('1');
            continue;
        }
        if (ch == '2') {
            handle_show();
            uart.write('1');
            continue;
        }
        if (ch == '3') {
            handle_clear();
            uart.write('1');
            continue;
        }
        uart.write('0');
    }
}

