# Exhaustively test all possible orderings of operations
# for a given number of threads.


# Generate the initial list of tests
time python gentest.py 2 9 > input.txt

for i in {1..99} ; do

	iter=$(printf "%02d" $i)
	lines=$(wc -l input.txt | cut -f1 -d\ )
	echo $iter $lines
	if test $lines -eq 0 ; then 
		break
	fi

	# Run the tests
	time python -m unittest discover &> out-$iter

	# Rename the output files per iteration
	for j in input passed failed todo ; do
		mv $j.txt $j-$iter.txt
	done

	# Last iteration's todo is next iteration's input
	cp todo-$iter.txt input.txt 
done