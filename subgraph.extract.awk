BEGIN {
    if (!SUBGRAPH_NAME) {
        print "Must provide subgraph name.";
        exit 1;
    }
}

/^digraph/ || (/^\t[^\t]/ && /;$/) || ($0 ~ SUBGRAPH_NAME)

END {
    print "\t}\n}";
}
