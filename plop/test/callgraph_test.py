import unittest

from plop.callgraph import CallGraph, Node

class SimpleCallgraphTest(unittest.TestCase):
    def setUp(self):
        graph = CallGraph()
        graph.add_stack([Node(1), Node(2)], dict(time=1))
        graph.add_stack([Node(1), Node(3)], dict(time=3))
        graph.add_stack([Node(1), Node(2), Node(3)], dict(time=7))
        graph.add_stack([Node(1), Node(4), Node(2), Node(3)], dict(time=2))
        self.graph = graph

    def test_basic_attrs(self):
        """ nodes were correctly added to the graph """
        self.assertEqual(len(self.graph.nodes), 4)
        self.assertEqual(len(self.graph.edges), 5)

    def test_top_edges(self):
        """ the callgraph can retrieve the top edges """
        top_edges = self.graph.get_top_edges('time', 3)
        summary = [(e.parent.id, e.child.id, e.weights['time']) for e in top_edges]
        self.assertEqual(summary, [
            (2, 3, 9),
            (1, 2, 8),
            (1, 3, 3),
        ])

    def test_top_nodes(self):
        """ the callgraph can retrieve the top nodes """
        top_nodes = self.graph.get_top_nodes('time', 2)
        summary = [(n.id, n.weights['time']) for n in top_nodes]
        self.assertEqual(summary, [
            (3, 12),
            (2, 1),
        ])
