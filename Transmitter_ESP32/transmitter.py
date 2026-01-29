import network
import urequests
import time
from machine import Pin

# ================= WIFI DETAILS =================
SSID = "Samiksha"
PASSWORD = "samysays"

# ================= THINGSPEAK ===================
WRITE_API_KEY = "4TQCHLKMIJQD006Q"

# ================= RSSI LIMITS ==================
WEAK_RSSI = -70
RSSI_MIN = -95
RSSI_MAX = -30

# ================= PIN SETUP ====================
TRIG_PIN = 5
ECHO_PIN = 18
BUZZER_PIN = 27

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
buzzer = Pin(BUZZER_PIN, Pin.OUT)
buzzer.value(0)

# ================= WIFI INIT ====================
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.disconnect()
time.sleep(1)

print("Connecting to WiFi...")
wifi.connect(SSID, PASSWORD)

timeout = 15
while not wifi.isconnected() and timeout > 0:
    print("Waiting for WiFi...")
    time.sleep(1)
    timeout -= 1

if wifi.isconnected():
    print("WiFi Connected ✅")
    print("IP:", wifi.ifconfig())
else:
    print("WiFi FAILED ❌")

# ================= FUNCTIONS ====================

def get_distance():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    timeout = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout) > 30000:
            return -1

    start = time.ticks_us()

    timeout = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), timeout) > 30000:
            return -1

    end = time.ticks_us()
    return (time.ticks_diff(end, start) * 0.0343) / 2


def read_rssi():
    if not wifi.isconnected():
        return None

    rssi = wifi.status("rssi")
    if rssi is None:
        return None

    if RSSI_MIN <= rssi <= RSSI_MAX:
        return rssi

    return None


def buzzer_alert(rssi):
    if rssi is None:
        buzzer.value(0)
        return

    if rssi <= WEAK_RSSI:
        buzzer.value(1)
        time.sleep(0.3)
        buzzer.value(0)
    else:
        buzzer.value(0)


def send_to_thingspeak(rssi, distance):
    if not wifi.isconnected():
        print("WiFi not connected → Upload skipped")
        return

    try:
        url = (
            "http://api.thingspeak.com/update?"
            "api_key=" + WRITE_API_KEY +
            "&field1=" + str(rssi) +
            "&field2=" + str(distance)
        )

        r = urequests.get(url)
        response = r.text
        r.close()

        if response != "0":
            print("ThingSpeak Upload SUCCESS ✅ Entry ID:", response)
        else:
            print("ThingSpeak Upload FAILED ❌ (Rate limit / API key issue)")

    except Exception as e:
        print("ThingSpeak Error:", e)

# ================= MAIN LOOP ====================
while True:
    distance = get_distance()
    rssi = read_rssi()

    if rssi is not None:
        print("RSSI:", rssi, "dBm")
    else:
        print("RSSI: INVALID")

    print("Distance:", distance)

    buzzer_alert(rssi)

    if rssi is not None:
        send_to_thingspeak(rssi, distance)

    print("--------------------------------")
    time.sleep(15)
