CXXFLAGS+=-g -Wall -std=c++11
LDLIBS+=-lglut -lGL -lGLU -lGLEW -lm
all: SutherlandHodgman
SutherlandHodgman: SutherlandHodgman.o zpr.o
	g++ $(CFLAGS) -o SutherlandHodgman zpr.o $< $(LDLIBS) 
clean:
	rm -f *.o
