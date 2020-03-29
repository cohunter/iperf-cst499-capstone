# Android

---

[toc]

## Building & Cross-compiling

### Build Go programs

```bash
export CGO_ENABLED=0
export GOOS=linux
export GOARCH=arm
go build client.go
```

### Build iPerf 2

1. Get the NDK[^Source]
   * https://dl.google.com/android/repository/android-ndk-r21-linux-x86_64.zip

[^Source]: https://developer.android.com/ndk/downloads/index.html

### Build iPerf 3

## Running via ADB [^1]

```bash
adb push iperf2 /data/local/tmp
adb push iperf3 /data/local/tmp
adb shell /data/local/tmp/iperf2
adb shell /data/local/tmp/iperf3
```

[^1]: https://android.stackexchange.com/a/209139

### Testing & Data Collection

#### On-Device

Busybox is the easiest method to run the program in the background on Android after disconnecting from the computer. This does NOT require root.

1. Download the appropriate ARM binary from the Busybox website[^2]
   * To check which ABI your device supports, run the following command:
   * `adb shell getprop ro.product.cpu.abi` [^3][^4]
2. Push the binary to /data/local/tmp
   * `adb push busybox /data/local/tmp`
3. Run the client using the `nohup` applet
   * `adb shell '/data/local/tmp/busybox nohup /data/local/tmp/client > /data/local/tmp/client.out'`
   * Note the single quotes around the command
4. Check output at any time by reconnecting the phone to a computer
   * `adb shell tail -f /data/local/tmp/client.out`
   * `adb shell cat /data/local/tmp/client.out > client.out`
5. To stop, either reboot the device or run the following command:
   * `adb shell killall sh`

[^2]: https://busybox.net/FAQ.html#getting_started

[^3]: https://stackoverflow.com/a/46751394
[^4]: https://developer.android.com/ndk/guides/abis

#### Tethered

Create stub scripts to call iPerf over adb instead of locally, then run the client with them in your PATH.  
_Remember to `chmod u+x iperf` and `chmod u+x iperf3` after creating the scripts._

##### iperf

```bash
#!/bin/sh
adb shell /data/local/tmp/iperf2
```

##### iperf3

```bash
#!/bin/sh
adb shell /data/local/tmp/iperf3
```

##### client

```bash
PATH=. client
```

