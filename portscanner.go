package main

import (
	"fmt"
	"net"
	"os"
	"strings"
	"sync"
	"time"
)

const GOROUTINES = 25  // How many ports to check simultaneously
const MIN_PORT = 1     // Lowest port number to check
const MAX_PORT = 65535 // Highest port number to check

func scanPort(host string, port int) bool {
	// Return values: true = connected; false = failed

	c, err := net.Dial("tcp", fmt.Sprintf("%s:%d", host, port))
	if err != nil {
		return false
	}
	c.Close()

	// Log a successful connection
	return true
}

func usage() {
	fmt.Printf("Usage: %s hostname", os.Args[0])
}

// This runs a goroutine that just loops forever and will die when the app finishes
func printStatus(host string, numPorts int, portsChecked *int) {
	go func() {
		fmt.Printf("\n")
		for i := 0; ; i = i % 3 {
			fmt.Printf("\rScanning %s [%d/%d]%s  ", host, *portsChecked, numPorts, strings.Repeat(".", i+1))
			time.Sleep(100 * time.Millisecond)
			i++
		}
	}()
}

func main() {
	var openPorts []int
	var wg sync.WaitGroup // number of working goroutines
	var portsChecked int

	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}

	var host = os.Args[1]

	// Channel to fill with all port numbers to be checked. Buffered to the size
	// of all ports to be checked to prevent deadlocking.
	uncheckedPorts := make(chan int, MAX_PORT+1-MIN_PORT)

	for i := MIN_PORT; i <= MAX_PORT; i++ {
		uncheckedPorts <- i
		wg.Add(1)
	}

	printStatus(host, len(uncheckedPorts), &portsChecked)

	// Create however many goroutines requested
	for i := 0; i < GOROUTINES; i++ {
		go func() {
			for port := range uncheckedPorts {
				if portOpen := scanPort(host, port); portOpen {
					openPorts = append(openPorts, port)
				}
				wg.Done()
				portsChecked++
			}
		}()
	}

	// Wait for everything to finish, then print the results
	wg.Wait()
	fmt.Printf("\nOpen ports: %d\n", openPorts)
}
