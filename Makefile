all: hictkR.so

hictkR.so: src/hictkR.cpp
	R CMD SHLIB src/hictkR.cpp -o src/hictkR.so

clean:
	rm -f src/*.o
	rm -f src/*.so
