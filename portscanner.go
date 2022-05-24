package main

import (
	"fmt"
	"net"
	"os"
	"sync/atomic"
	"time"
)

const GOROUTINES = 25  // How many ports to check simultaneously
const MIN_PORT = 1     // Lowest port number to check
const MAX_PORT = 65535 // Highest port number to check

func scanPort(host string, port int) bool {
	// Return values: true = connected; false = failed
	_, err := net.Dial("tcp", fmt.Sprintf("%s:%d", host, port))
	if err != nil {
		return false
	}

	// Log a successful connection
	return true
}

func usage() {
	fmt.Printf("Usage: %s hostname", os.Args[0])
}

// This runs a goroutine that just loops forever and will die when the app finishes
func printStatus(host string, openPorts chan int, portsChecked *uint32) {
	go func() {
		var spinner = "-\\|/"
		fmt.Printf("\n")
		for i := 0; ; i = i % 3 {
			fmt.Printf("%s Scanning %s [%d/%d] Open ports:%d\r",
				string(spinner[i]), host, *portsChecked, cap(openPorts), len(openPorts))
			time.Sleep(100 * time.Millisecond)
			i++
		}
	}()
}

func main() {
	//var openPorts []int
	portCount := MAX_PORT + 1 - MIN_PORT
	var portsChecked uint32                   // uint16 would be enough for a single system
	goroutines := make(chan bool, GOROUTINES) // concurrency control
	openPorts := make(chan int, portCount)    // Store list of open ports, concurrency-safe, buffered

	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}

	var host = os.Args[1]

	printStatus(host, openPorts, &portsChecked)

	for port := MIN_PORT; port <= MAX_PORT; port++ {
		goroutines <- true // Wait until allowed to go
		go func(port int) {
			defer func() { <-goroutines }() // release lock when done
			// Check the port
			if portOpen := scanPort(host, port); portOpen {
				openPorts <- port
			}
			atomic.AddUint32(&portsChecked, 1)
		}(port)
	}

	// Wait for everything to finish by waiting until nothing left in channel, then print the results
	for i := 0; i < cap(goroutines); i++ {
		goroutines <- true
	}

	// Close openPorts channel once everything is done, so we can pull all values off it to display
	close(openPorts)

	//fmt.Printf("\nOpen ports: %d\n", openPorts)
	fmt.Printf("\nOpen ports:\n\t[ ")

	for p := range openPorts {
		fmt.Printf("%d ", p)
	}
	fmt.Printf("]\n")
}
