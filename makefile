test:
	python -m unittest discover

exhaustive:
	bash runtests.sh

clean:
	rm -f *.txt out*
