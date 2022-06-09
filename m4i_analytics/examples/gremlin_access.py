# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 15:38:25 2018

@author: andre
"""

#%%
from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.traversal import T, P, Operator

if __name__ == '__main__': 
    
    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection('ws://127.0.0.1:8182/gremlin','g',username='root',password='Aurelius18UVA'))
    print(graph)
    print(g)
    
    print(g.V().count().next())
    print(g.E().count().next())
    
    #%%
    j = g.addV('test_jupiter').property('name', 'jupiter').property('age', 3700).next()
    m = g.addV('test_mars').property('name', 'mars').property('age', 3500).next()
    
    g.addE("created").from_(j).to(m).next();
    
    person = g.V(j)
    lop = g.V()
    
    g.V(person).addE('hallo').to(lop).next()
    a.iterate()
    g.addE(j,'test',m).next()
    
    q = g.V().has("name",'jupiter').has("age",3700)
    for ii in q:
        print(ii)
    #%%
    print(g.E().next())
    a = g.addV('insert').property('id', '0815').property('pronoun', 'me')
    b = g.addV('insert').property('id', '1744').property('pronoun','you')
    
    e1 = a.addE('knows').to(b).property('relation','self').iterate()
    print(g.E().count().next())
    #%%
    b2 = g.addV('insert').property('id', '1800').property('pronoun','you').next()
    a1 = g.V().has('id','0815')
    b22 = g.V().has('id','1800')
    e2 = a1.addE('knows').to(b22).property('relation','self').iterate()
    print(g.E().count().next())
    
    #%%
    a = g.addV('insert').property('id', '0820').property('pronoun', 'me').next()
    
    a12 = g.V(a.id['@value'])
    b22 = g.V().has('id','1800')
    e2 = a12.addE('knows').to(b22).property('relation','self').iterate()
    print(g.E().count().next())