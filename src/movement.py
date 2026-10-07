import math

def approach(current, target, distance):
    if abs(target - current) <= distance:
        return target, True
    return current + math.copysign(distance, target - current), False
