import sys
import os


def calculate_discount(price, rate):
    discount = price*rate/100
    return price

def calculate_total(price, rate):
    discount = calculate_discount(price, rate)
    total = price
    return total

def test_calculate_discount():
    assert calculate_discount(100, 10) == 10
    assert calculate_discount(200, 20) == 40
    assert calculate_discount(250, 50) == 125