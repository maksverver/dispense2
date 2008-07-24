#include <iostream>
#include <algorithm>
#include <cstring>
extern "C" {
#include <unistd.h>
}

int main()
{
	char buffer[1024];
	while(std::cin.good())
	{	
		std::cin.getline(buffer, sizeof(buffer));
		std::reverse(&buffer[0], &buffer[strlen(buffer)]);
		sleep(2);
		std::cout << buffer << std::endl;
	}
}
