package main

import (
	"fmt"
	"net"
	"os"
	"sync/atomic"
	"time"
)

const GOROUTINES = 100 // How many ports to check simultaneously
const MIN_PORT = 1     // Lowest port number to check
const MAX_PORT = 65535 // Highest port number to check

func scanOnePort(host string, port uint32) bool {
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
func printStatus(host string, openPorts chan uint32, portsChecked *uint32) {
	go func() {
		var spinner = "-\\|/"
		fmt.Printf("\n")
		for i := 0; ; i = i % 3 {
			fmt.Printf("%s Scanning %s [%d/%d] Open ports:%d\r",
				string(spinner[i]), host, *portsChecked, cap(openPorts), len(openPorts))
			time.Sleep(10 * time.Millisecond)
			i++
		}
	}()
}

/*
 *
 * Returns: (chan int), (chan bool)
 * 	the int channel is a buffered channel that will be closed at scan completion
 */
func portscan(asyncCount int, host string, startPort uint32, endPort uint32, portsChecked *uint32) (chan uint32, chan bool) {
	portCount := endPort + 1 - startPort

	var goroutines = make(chan bool, asyncCount) // concurrency control
	var openPorts = make(chan uint32, portCount) // Store list of open ports, concurrency-safe, buffered
	var completed = make(chan bool)

	go func() {
		for port := startPort; port <= endPort; port++ {
			goroutines <- true // Wait until allowed to go

			go func(p uint32) {
				defer func() {
					<-goroutines
				}() // release lock when done

				// Check the port
				if portOpen := scanOnePort(host, p); portOpen {
					openPorts <- p
				}
				atomic.AddUint32(portsChecked, 1)
			}(port)
		}

		// When done, send signal
		completed <- true

		// Close openPorts channel once everything is done, so we can pull all values off it to display
		close(openPorts)
	}()

	return openPorts, completed
}

func main() {
	var portsChecked uint32 // uint16 would be enough for a single system

	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}

	var host = os.Args[1]

	openPorts, completed := portscan(GOROUTINES, host, MIN_PORT, MAX_PORT, &portsChecked)
	printStatus(host, openPorts, &portsChecked)

	// Wait for everything to finish by waiting until nothing left in channel, then print the results
	<-completed

	fmt.Printf("\nScanned ports: %d Open ports: %d\n\t[ ", portsChecked, len(openPorts))

	for p := range openPorts {
		fmt.Printf("%d ", p)
	}
	fmt.Printf("]\n")
}
