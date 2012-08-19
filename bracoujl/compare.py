# compare.py - Makes comparison between two graphs.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

def compare_graphs(graph1, graph2):
    addr_checked, stack, blocks_diff = [], [0x10000], 0
    while stack:
        addr, block1, block2 = stack.pop(), None, None
        if addr in addr_checked:
            continue
        addr_checked.append(addr)
        try: block1 = graph1.nodes[addr]
        except KeyError: pass
        try: block2 = graph2.nodes[addr]
        except KeyError: pass
        if block1 is None or block2 is None:
            print 'One of the graphs doesn\'t contain %04X addr.' % addr
            if block1 is not None:
                print 'In graph 1:'
                block1.sumary()
                stack.extend(list(block1.to))
            if block2 is not None:
                print 'In graph 2:'
                block2.sumary()
                stack.extend(list(block2.to))
            print '=' * 40
            blocks_diff += 1
            continue
        if not (block1 == block2):
            block1.sumary()
            print '- ' * 20
            block2.sumary()
            print '=' * 40
            blocks_diff += 1
        stack.extend(list(block1.to | block2.to))
    print 'Found %d differences.' % blocks_diff
