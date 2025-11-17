### Satisfactory tool splitter

A tool to help calculate how to split conveyors in Satisfactory into specific ratios.

## Why?

Your factory produces A+B+C items per minute.
A+B of these items, you need for your production chain inside that factory.

The remaining C of them, you need to transport via vehicles to another factory.

If you used a simple splitter, (A+B+C)/3 items would be queued for transport via vehicle.
Because vehicles transport _everything_ you have available, your local
factory will be starved and the destination factory will be swamped with
incoming items  or vice versa.

Using accurate conveyer splitting, you can ensure that the offshore factory
will receive exactly C items per minute, not less and not more.

## Usage examples

    python3 smartsplit 10 20

![Graph for 10:20](images/10_20.png)

    python3 smartsplit 54 51

![Graph for 54:51](images/54_51.png)

    python3 smartsplit 1 2 3 4 5 6

![Graph for 1:2:3:4:5:6](images/1_2_3_4_5_6.png)

    python3 smartsplit 4.5 6.5 3

![Graph for 4.5:6.5:3](images/4.5_6.5_3.png)

## Graphviz

Output is done with a Graphviz Digraph. From each node, there is an arrow pointing to where it goes.
When graphing, nodes are displayed in a few different ways depending on what it represents.

Inputs are houses, Outputs are inverted houses, splitters are Diamonds and mergers are Squares.
Currently, a chain of mergers will be condensed into a single merger.

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Thanks

Thanks to [IceMoonMagic](https://github.com/IceMoonMagic/Satisfactory-Splitter-Calculator)
whose splitter source code I read for ideas.
His splitter has more features (such as taking into account different tool belt speeds),
but my tool produces chains with fewer nodes.
