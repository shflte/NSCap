main: main.o
	g++ main.o -o main -lpcap
	rm main.o

main.o: 109550100_hw1.cpp
	g++ -c 109550100_hw1.cpp -o main.o

all: 109550100_hw1.cpp

109550100_hw1.cpp:
	echo compile 109550100_hw1.cpp

clean:
	rm *.o