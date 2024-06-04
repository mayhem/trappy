from abc import abstractmethod
from time import sleep

class Effect:

    def __init__(self, driver):
        self.driver = driver

    def scroll(self, pattern, delay, buf, row_index, num_rows):
        direction = 1 if num_rows > 0 else 0;
        for j in range(abs(num_rows)):
            row = pattern.get(row_index)
            self.shift(buf, row, direction)
            self.driver.set(buf)
            sleep(delay)
            row_index += 1

        return row_index

    def shift(self, buf, new_row, direction):
        for strip in range(self.driver.strips):
            begin = strip * self.driver.leds
            end = (strip + 1) * self.driver.leds;
            if direction == 1:
                temp = buf[begin:end-1]
                temp.insert(0, new_row[strip])
                buf[begin:end] = temp
            else:
                temp = buf[begin+1:end]
                temp.append(new_row[strip])
                buf[begin:end] = temp


    @abstractmethod
    def run(self, timeout):
        pass
